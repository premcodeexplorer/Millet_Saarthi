"""MilletSaarthi Planner — decides the next group of agents to run.

This is the *agentic brain* of the orchestrator: after every step it inspects
the current state and returns the next parallel task group, with a
human-readable justification. Dynamic routing, conditional skipping, and
reflection loops all live here.
"""
from __future__ import annotations

from typing import Optional


# Thresholds used by the planner — exposed as module constants so they can be
# tuned or overridden from tests/UI.
LOW_QUALITY_CONFIDENCE = 0.30     # below this -> human review, abort pipeline
WEAK_QUALITY_CONFIDENCE = 0.55    # below this -> reflection retry with enhanced image
HIGH_MOISTURE = 16.0              # above this -> urgent path, skip price trend
MAX_REFLECTION_RETRIES = 1


class Planner:
    """State-driven agentic planner.

    Each call to :meth:`next_group` returns a list of agent names that may
    run **in parallel** (independent of each other), plus a reason string
    explaining *why* the planner chose that step. Returns an empty list when
    the pipeline is complete.
    """

    def next_group(self, state: dict) -> tuple[list[str], str]:
        # ---- 1. Kick-off: classify grain + resolve location in parallel ----
        if "millet" not in state and "geo_done" not in state:
            return (
                ["quality", "geocode"],
                "Initial step — classify grain and geocode farmer location "
                "(independent, run in parallel)",
            )

        # ---- 1b. Invalid image (blurry) gate ---------------------------------
        if state.get("invalid_image"):
            if "action" not in state:
                state["action"] = "ERROR"
                state["reason"] = state.get("error", "Invalid image uploaded.")
            return ([], "Image rejected (blurry). Pipeline aborted.")

        # ---- 2. Reflection gate: quality confidence check ------------------
        q_conf: Optional[float] = state.get("quality_score")
        retries = state.get("reflection_retries", 0)

        if q_conf is not None and q_conf < LOW_QUALITY_CONFIDENCE:
            return (
                ["human_review"],
                f"Quality confidence {q_conf:.2f} < {LOW_QUALITY_CONFIDENCE} — "
                "pipeline short-circuited, routing to human review",
            )

        if (
            q_conf is not None
            and q_conf < WEAK_QUALITY_CONFIDENCE
            and retries < MAX_REFLECTION_RETRIES
            and state.get("retry_image_path") is None
        ):
            return (
                ["quality_retry"],
                f"Quality confidence {q_conf:.2f} < {WEAK_QUALITY_CONFIDENCE} — "
                "reflection loop: re-run Agent 1 on contrast-enhanced image",
            )

        # ---- 3. Urgency gate: wet grain short-circuits price analysis ------
        moisture = state.get("moisture", 12.0)
        if moisture > HIGH_MOISTURE and "best_market" not in state and "weather" not in state:
            return (
                ["market", "weather"],
                f"Moisture {moisture}% > {HIGH_MOISTURE}% — urgent path, "
                "running market + weather in parallel (will skip price trend)",
            )

        # ---- 4. Normal path: market + weather in parallel ------------------
        if "best_market" not in state and "weather" not in state:
            return (
                ["market", "weather"],
                "Normal path — running market comparison and weather forecast "
                "in parallel (both need only lat/lon)",
            )

        # If only one of the two ran (e.g. market failed), still run the other
        if "weather" not in state:
            return (["weather"], "Fetching weather forecast")
        if "best_market" not in state and state.get("market_error") is None:
            return (["market"], "Running market comparison")

        # ---- 5. Price: baseline at the nearest APMC ------------------------
        if "expected_price" not in state and moisture <= HIGH_MOISTURE:
            return (
                ["price"],
                "Running price agent — baseline + 1-month trend at nearest APMC "
                "(uses Agent 3's district to stay in-distribution)",
            )

        # ---- 6. Decision: final recommendation -----------------------------
        if "action" not in state:
            if moisture > HIGH_MOISTURE:
                return (
                    ["decision"],
                    "Running decision agent in URGENT mode (wet grain — trend "
                    "analysis skipped)",
                )
            return (
                ["decision"],
                "Running decision agent — fusing quality + price + market + "
                "weather + festival + shelf life",
            )

        # ---- 7. Explainer: Marathi/English natural language summary --------
        if "explanation" not in state:
            return (
                ["explainer"],
                "Running explainer (Agent 5) — Gemini LLM converts the "
                "structured decision into a Marathi + English paragraph "
                "for the farmer",
            )

        # ---- 8. Done -------------------------------------------------------
        return ([], "Pipeline complete")
