"""Agent 5 — Farmer Explainer (Gemini-powered natural-language layer).

Takes the orchestrator's structured output (millet, grade, market, price,
weather, festival, decision) and generates a friendly Marathi + English
paragraph that the farmer can read directly. The structured ML/rule outputs
remain authoritative — the LLM is *only* a presentation layer.

Falls back to a deterministic template when the API key is missing or the
network call fails so the demo never breaks mid-flow.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.config import GEMINI_API_KEY


MILLET_MR = {"jowar": "ज्वारी", "bajra": "बाजरी", "ragi": "नाचणी"}


PROMPT_TEMPLATE = """You are a friendly Indian agricultural advisor speaking to a smallholder millet farmer. Convert the structured decision below into TWO short paragraphs:

1. First in Marathi (Devanagari script) — addressed as "शेतकरी साहेब" (Sir/Brother farmer)
2. Then in English — addressed as "Sir"

Each paragraph: 3 to 4 sentences. Friendly but practical tone. Tell them WHAT to do (sell/wait/store), WHERE (which APMC), the EXACT price, and ONE main reason (weather, festival, or shelf life). Do not invent any numbers — use only the values given below.

DECISION DATA:
- Grain: {millet} Grade {grade}, {quantity} quintals
- Action: {action}
- Best market: {best_market} ({distance_km} km away)
- Net price after costs: ₹{net_price}/quintal
- Total revenue: ₹{total_revenue}
- Trend: {trend}
- Rain next 3 days: {rain_mm} mm
- Weather note: {weather_summary}
- Shelf life: {shelf_days} days ({shelf_note})
- Next festival: {festival_name} in {festival_days} days ({festival_pct}% demand bump — {festival_reason})
- Reasoning hint: {decision_reason}

OUTPUT FORMAT (exactly):
MARATHI:
<3-4 sentence paragraph in Devanagari>

ENGLISH:
<3-4 sentence paragraph in English>
"""


class ExplainerAgent:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.log = logging.getLogger("ExplainerAgent")
        key = api_key or GEMINI_API_KEY
        self.ready = False
        self.model = None
        if not key:
            self.log.warning("GEMINI_API_KEY missing — explainer in mock mode")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            self.ready = True
            self.log.info("Loaded Gemini 2.0 Flash for Agent 5")
        except Exception as e:
            self.log.warning(f"Failed to init Gemini ({e}) — explainer in mock mode")

    def explain(self, state: dict) -> dict:
        """Return {'marathi': str, 'english': str, 'source': str}."""
        prompt_data = self._extract(state)
        if not self.ready:
            return self._template(prompt_data, source="template")

        try:
            prompt = PROMPT_TEMPLATE.format(**prompt_data)
            response = self.model.generate_content(prompt)
            text = (response.text or "").strip()
            marathi, english = self._parse(text)
            if not marathi or not english:
                self.log.warning("Gemini output missing one language — falling back")
                return self._template(prompt_data, source="template_fallback")
            return {"marathi": marathi, "english": english, "source": "gemini"}
        except Exception as e:
            self.log.warning(f"Gemini call failed ({e}) — falling back to template")
            return self._template(prompt_data, source="template_fallback")

    def predict(self, state: dict) -> dict:
        """Orchestrator-compatible alias — wraps result under explanation key."""
        return {"explanation": self.explain(state)}

    @staticmethod
    def _extract(state: dict) -> dict:
        best = state.get("best_market") or {}
        weather = state.get("weather") or {}
        shelf = state.get("shelf_life") or {}
        fest = state.get("next_festival") or {}
        return {
            "millet": (state.get("millet") or "millet").title(),
            "grade": state.get("grade") or "B",
            "quantity": state.get("quantity_quintal") or 1,
            "action": state.get("action") or "SELL",
            "best_market": best.get("market") or best.get("name") or "the nearest APMC",
            "distance_km": round(best.get("distance_km") or 0, 1),
            "net_price": round(
                best.get("net_price_per_q")
                or best.get("net_price")
                or state.get("expected_price")
                or 0, 2),
            "total_revenue": round(
                best.get("total_net_revenue")
                or best.get("total_net")
                or state.get("expected_total_revenue")
                or 0, 2),
            "trend": state.get("trend") or "stable",
            "rain_mm": weather.get("rain_mm_3d", 0),
            "weather_summary": weather.get("summary") or "Conditions are normal",
            "shelf_days": shelf.get("days", "—"),
            "shelf_note": shelf.get("note") or "Storage condition not assessed",
            "festival_name": fest.get("name") or "no major festival",
            "festival_days": fest.get("days_away", "—"),
            "festival_pct": fest.get("spike_pct", 0),
            "festival_reason": fest.get("reason") or "",
            "decision_reason": state.get("reason") or "",
        }

    @staticmethod
    def _parse(text: str) -> tuple[str, str]:
        marathi, english = "", ""
        if "MARATHI:" in text and "ENGLISH:" in text:
            mar_part = text.split("MARATHI:", 1)[1]
            mar_part, eng_part = mar_part.split("ENGLISH:", 1)
            marathi = mar_part.strip()
            english = eng_part.strip()
        return marathi, english

    @staticmethod
    def _template(d: dict, source: str) -> dict:
        action_raw = str(d["action"] or "SELL").upper()
        action_en = {"SELL_NOW": "sell now", "URGENT_SELL": "urgently sell",
                     "WAIT": "wait", "HOLD_CAUTION": "hold (with caution)",
                     "HUMAN_REVIEW": "consult an expert"}.get(action_raw, "sell")
        action_mr = {"SELL_NOW": "आता विकणे", "URGENT_SELL": "तातडीने विकणे",
                     "WAIT": "थांबणे", "HOLD_CAUTION": "सावधगिरीने ठेवणे",
                     "HUMAN_REVIEW": "तज्ञांचा सल्ला घेणे"}.get(action_raw, "विकणे")
        millet_mr = MILLET_MR.get(str(d["millet"]).lower(), d["millet"])
        marathi = (
            f"शेतकरी साहेब, तुमची ग्रेड {d['grade']} {millet_mr} ({d['quantity']} क्विंटल) "
            f"{d['best_market']} येथे {action_mr} सर्वोत्तम आहे. "
            f"तुम्हाला सर्व खर्च वजा करून ₹{d['net_price']}/क्विंटल मिळेल — एकूण ₹{d['total_revenue']}. "
            f"पुढील ३ दिवसांत {d['rain_mm']} मिमी पाऊस अपेक्षित आहे; "
            f"धान्य सुरक्षित ठेवण्याचा कालावधी {d['shelf_days']} दिवस आहे."
        )
        english = (
            f"Sir, your Grade {d['grade']} {d['millet']} ({d['quantity']} quintals) is best "
            f"to {action_en} at {d['best_market']} ({d['distance_km']} km away). "
            f"Net price ₹{d['net_price']}/quintal — total revenue ₹{d['total_revenue']}. "
            f"Rain next 3 days: {d['rain_mm']} mm. Storage life: {d['shelf_days']} days."
        )
        return {"marathi": marathi, "english": english, "source": source}
