"""MilletSaarthi Orchestrator — agentic state-driven executor.

This is NOT a fixed 1->2->3->4 pipeline. A :class:`Planner` inspects the
current state after every step and decides the next group of agents to run,
possibly in parallel. The orchestrator supports:

- Dynamic routing (planner re-evaluates after each step)
- Parallel execution of independent agents via ``ThreadPoolExecutor``
- Conditional short-circuiting (e.g. low-quality image -> human review)
- Reflection loop (Agent 4 verification can request Agent 1 rerun via planner)
- Degraded-mode execution when an external call fails

Every decision the planner makes is recorded in ``state["agentic_trace"]``
so the UI / paper can show *why* each step ran.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from PIL import Image, ImageEnhance

from agents.decision_agent import DecisionAgent
from agents.explainer import ExplainerAgent
from agents.market_agent import MarketAgent
from agents.price_agent import PriceAgent
from agents.quality_agent import QualityAgent
from app.planner import Planner, WEAK_QUALITY_CONFIDENCE


MAX_PLANNER_ITERATIONS = 12


class MilletSaarthiOrchestrator:
    def __init__(self) -> None:
        self.log = logging.getLogger("Orchestrator")
        self.log.info("Loading agents...")
        self.quality = QualityAgent()
        self.price = PriceAgent()
        self.market = MarketAgent(price_agent=self.price)
        self.decision = DecisionAgent()
        self.explainer = ExplainerAgent()
        self.planner = Planner()
        # Tool registry — planner picks agent by name
        self._tools: dict[str, Callable[[dict], dict]] = {
            "quality":       self._run_quality,
            "geocode":       self._run_geocode,
            "market":        self._run_market,
            "weather":       self._run_weather,
            "price":         self._run_price,
            "decision":      self._run_decision,
            "explainer":     self._run_explainer,
            "quality_retry": self._run_quality_retry,
            "human_review":  self._run_human_review,
        }
        self.log.info("All agents ready — %d tools registered", len(self._tools))

    # ====================================================================
    # Public entry point
    # ====================================================================
    def run(
        self,
        image_path: str,
        location_text: str,
        quantity_quintal: float,
        moisture: float = 12.0,
        year: Optional[int] = None,
        month: Optional[int] = None,
        max_distance_km: float = 300,
    ) -> dict[str, Any]:
        now = datetime.now()
        state: dict[str, Any] = {
            "image_path": image_path,
            "location_text": location_text,
            "quantity_quintal": quantity_quintal,
            "moisture": moisture,
            "year": year or now.year,
            "month": month or now.month,
            "max_distance_km": max_distance_km,
            "pipeline": [],
            "agentic_trace": [],
            "reflection_retries": 0,
        }

        for iteration in range(MAX_PLANNER_ITERATIONS):
            group, reason = self.planner.next_group(state)
            if not group:
                state["agentic_trace"].append({
                    "iter": iteration,
                    "action": "done",
                    "reason": reason,
                })
                break

            t0 = time.perf_counter()
            self._execute_parallel(group, state)
            dur_ms = int((time.perf_counter() - t0) * 1000)

            state["agentic_trace"].append({
                "iter": iteration,
                "action": "run_parallel" if len(group) > 1 else "run",
                "tasks": group,
                "reason": reason,
                "duration_ms": dur_ms,
            })

        return state

    # ====================================================================
    # Parallel executor
    # ====================================================================
    def _execute_parallel(self, group: list[str], state: dict) -> None:
        """Run a group of agents concurrently and merge results into state."""
        if len(group) == 1:
            name = group[0]
            result = self._safe_call(name, state)
            self._merge(state, name, result)
            return

        # Use a thread pool — all agents are I/O or GIL-releasing torch ops,
        # so threads give real parallelism for the network-bound ones.
        with ThreadPoolExecutor(max_workers=len(group)) as ex:
            futures = {ex.submit(self._safe_call, name, state): name for name in group}
            for fut in as_completed(futures):
                name = futures[fut]
                self._merge(state, name, fut.result())

    def _safe_call(self, name: str, state: dict) -> dict:
        """Invoke an agent tool with exception insulation."""
        fn = self._tools.get(name)
        if fn is None:
            return {"_status": "error", "_error": f"unknown tool: {name}"}
        try:
            out = fn(state) or {}
            out.setdefault("_status", "ok")
            return out
        except Exception as e:
            self.log.exception(f"Tool {name} failed")
            return {"_status": "error", "_error": str(e)}

    def _merge(self, state: dict, name: str, result: dict) -> None:
        status = result.pop("_status", "ok")
        error = result.pop("_error", None)
        state["pipeline"].append({
            "agent": name,
            "status": status,
            **({"error": error} if error else {}),
        })
        if status == "ok":
            state.update(result)

    # ====================================================================
    # Tool implementations (one per planner action)
    # ====================================================================
    def _run_quality(self, state: dict) -> dict:
        return self.quality.predict(state)

    def _run_quality_retry(self, state: dict) -> dict:
        """Reflection loop: re-run Agent 1 on a contrast-enhanced copy."""
        original = Path(state["image_path"])
        if not original.exists():
            return {"_status": "error", "_error": "original image missing for retry"}

        enhanced_path = original.with_name(original.stem + "_enhanced" + original.suffix)
        img = Image.open(original).convert("RGB")
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img = ImageEnhance.Sharpness(img).enhance(1.3)
        img = ImageEnhance.Brightness(img).enhance(1.1)
        img.save(enhanced_path)

        retry_state = {**state, "image_path": str(enhanced_path)}
        result = self.quality.predict(retry_state)
        result["retry_image_path"] = str(enhanced_path)
        result["reflection_retries"] = state.get("reflection_retries", 0) + 1
        # Only overwrite quality fields if the retry actually improved confidence
        old_conf = state.get("quality_score", 0)
        if result.get("quality_score", 0) <= old_conf:
            # Retry didn't help — keep old values but still mark retry done
            result = {
                "retry_image_path": str(enhanced_path),
                "reflection_retries": state.get("reflection_retries", 0) + 1,
                "reflection_note": (
                    f"Retry confidence {result.get('quality_score',0):.2f} did not "
                    f"exceed original {old_conf:.2f} — keeping original classification"
                ),
            }
        return result

    def _run_geocode(self, state: dict) -> dict:
        geo = self.market.geocode(state["location_text"])
        if "error" in geo:
            return {"_status": "error", "_error": geo["error"], "geo_done": True}
        return {
            "geo_done": True,
            "farmer_state": geo["state"],
            "farmer_district": geo["district"],
            "farmer_location": {
                "input": state["location_text"],
                "lat": geo["lat"],
                "lon": geo["lon"],
                "resolved": geo["display_name"],
                "district": geo["district"],
                "state": geo["state"],
            },
        }

    def _run_market(self, state: dict) -> dict:
        m_out = self.market.predict(state)
        if "error" in m_out:
            return {"_status": "error", "_error": m_out["error"], "market_error": m_out["error"]}
        return m_out

    def _run_weather(self, state: dict) -> dict:
        loc = state.get("farmer_location") or {}
        lat, lon = loc.get("lat"), loc.get("lon")
        if lat is None or lon is None:
            return {"_status": "error", "_error": "no lat/lon for weather"}
        weather = self.decision.fetch_weather(lat, lon)
        return {"weather": weather}

    def _run_price(self, state: dict) -> dict:
        return self.price.predict(state)

    def _run_decision(self, state: dict) -> dict:
        return self.decision.predict(state)

    def _run_explainer(self, state: dict) -> dict:
        return self.explainer.predict(state)

    def _run_human_review(self, state: dict) -> dict:
        return {
            "action": "HUMAN_REVIEW",
            "reason": (
                f"Quality confidence too low ({state.get('quality_score',0):.2f}) — "
                "image unclear. Please retake photo in good light on a clean surface."
            ),
            "status": "SUSPICIOUS",
            "risk": "HIGH",
            "issues": ["Quality confidence below actionable threshold"],
            "decision_insights": [
                "Pipeline halted by planner: cannot safely recommend without reliable grain identification.",
                "Action: retake photo (clean white background, direct light, grains spread in single layer).",
            ],
        }
