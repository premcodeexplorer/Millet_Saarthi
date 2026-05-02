"""Agent 4 — Decision Advisor.

Rule-based advisor that fuses outputs from Agents 1-3 with real-time weather
(Open-Meteo free forecast) and a fixed festival calendar to recommend whether
the farmer should SELL_NOW, WAIT, URGENT_SELL, HOLD_CAUTION, or pursue
GOVT_PROCUREMENT. Also performs cross-agent verification to flag suspicious
combinations.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

import requests

from app.config import OPEN_METEO_FORECAST_URL


# --- Static knowledge tables ----------------------------------------------

# Marathi names for the three millets we support
MILLET_MR = {"jowar": "ज्वारी", "bajra": "बाजरी", "ragi": "नाचणी"}

# Bilingual labels for actions surfaced in the farmer-facing paragraph
ACTION_EN = {
    "SELL_NOW": "sell now", "URGENT_SELL": "urgently sell",
    "WAIT": "wait", "HOLD_CAUTION": "hold (with caution)",
    "HUMAN_REVIEW": "consult an expert",
}
ACTION_MR = {
    "SELL_NOW": "आता विकणे", "URGENT_SELL": "तातडीने विकणे",
    "WAIT": "थांबणे", "HOLD_CAUTION": "सावधगिरीने ठेवणे",
    "HUMAN_REVIEW": "तज्ञांचा सल्ला घेणे",
}


SHELF_LIFE_RULES = [
    {"max_moisture": 12.0, "days": 30, "note": "Dry grain — safe for long storage"},
    {"max_moisture": 14.0, "days": 18, "note": "Borderline — safe for 2-3 weeks"},
    {"max_moisture": 100.0, "days": 8,  "note": "High moisture — urgent, spoilage risk"},
]

# Indian festivals with demand spikes for millets (expanded annually).
# Dates are for 2026; duplicate rows across years keep the lookup simple.
FESTIVALS = [
    {"date": "2026-01-14", "name": "Makar Sankranti",   "spike_pct": 15, "reason": "Til-gud laddoo + bajra bhakri demand"},
    {"date": "2026-03-04", "name": "Holi",              "spike_pct": 8,  "reason": "Puran poli and sweet preparations"},
    {"date": "2026-03-21", "name": "Gudi Padwa",        "spike_pct": 10, "reason": "Marathi new year — sweet rotis"},
    {"date": "2026-04-14", "name": "Ambedkar Jayanti",  "spike_pct": 5,  "reason": "Community bhandaras"},
    {"date": "2026-07-27", "name": "Ashadhi Ekadashi",  "spike_pct": 12, "reason": "Vari pilgrimage — bajra/jowar bhakri staple"},
    {"date": "2026-08-27", "name": "Ganesh Chaturthi",  "spike_pct": 15, "reason": "10-day festival + modak preparations"},
    {"date": "2026-10-12", "name": "Navratri",          "spike_pct": 20, "reason": "Fasting foods (ragi, bajra prominent)"},
    {"date": "2026-10-20", "name": "Dussehra",          "spike_pct": 12, "reason": "Festive feasts"},
    {"date": "2026-11-09", "name": "Diwali",            "spike_pct": 25, "reason": "Peak festive demand — sweets and snacks"},
    {"date": "2026-12-25", "name": "Christmas",         "spike_pct": 5,  "reason": "Winter festive baking"},
]


def shelf_life_days(moisture: float) -> dict:
    """Map moisture % to safe storage duration."""
    for rule in SHELF_LIFE_RULES:
        if moisture <= rule["max_moisture"]:
            return {"days": rule["days"], "note": rule["note"]}
    return {"days": 7, "note": "High moisture — very short shelf life"}


def next_festival(today: Optional[date] = None) -> Optional[dict]:
    """Return the next upcoming festival with days remaining, or None."""
    today = today or datetime.now().date()
    upcoming = []
    for f in FESTIVALS:
        d = datetime.strptime(f["date"], "%Y-%m-%d").date()
        if d >= today:
            upcoming.append((d, f))
    if not upcoming:
        return None
    d, f = min(upcoming, key=lambda x: x[0])
    return {
        "name": f["name"],
        "date": f["date"],
        "days_away": (d - today).days,
        "spike_pct": f["spike_pct"],
        "reason": f["reason"],
    }


# --- Agent class -----------------------------------------------------------

class DecisionAgent:
    def __init__(self) -> None:
        self.log = logging.getLogger("DecisionAgent")

    # ---------- weather ----------
    def fetch_weather(self, lat: float, lon: float) -> dict:
        """Open-Meteo 7-day forecast. Free, no API key. Returns summary dict."""
        try:
            r = requests.get(
                OPEN_METEO_FORECAST_URL,
                params={
                    "latitude": lat, "longitude": lon,
                    "daily": "precipitation_sum,precipitation_probability_max,temperature_2m_max",
                    "forecast_days": 7,
                    "timezone": "auto",
                },
                timeout=10,
            )
            data = r.json().get("daily", {})
            precip = data.get("precipitation_sum", []) or []
            prob   = data.get("precipitation_probability_max", []) or []
            tmax   = data.get("temperature_2m_max", []) or []
            if not precip:
                raise ValueError("empty forecast")

            rain_3d = sum(precip[:3])
            rain_7d = sum(precip[:7])
            max_prob_3d = max(prob[:3]) if prob else 0
            max_prob_7d = max(prob[:7]) if prob else 0
            hot_days = sum(1 for t in tmax[:7] if t and t >= 38)

            if rain_3d >= 25 or max_prob_3d >= 70:
                summary = f"Heavy rain likely in next 3 days ({rain_3d:.0f} mm, {max_prob_3d}% chance)"
            elif rain_7d >= 40:
                summary = f"Rain spread across next 7 days ({rain_7d:.0f} mm total)"
            elif hot_days >= 3:
                summary = f"Hot week ahead ({hot_days} days >= 38°C) — risk for stored grain"
            else:
                summary = "Clear and dry for the next week"

            return {
                "rain_mm_3d": round(rain_3d, 1),
                "rain_mm_7d": round(rain_7d, 1),
                "rain_prob_3d_pct": int(max_prob_3d),
                "rain_prob_7d_pct": int(max_prob_7d),
                "hot_days_7d": hot_days,
                "summary": summary,
                "source": "open-meteo",
            }
        except Exception as e:
            self.log.warning(f"Open-Meteo failed: {e} — using neutral weather")
            return {
                "rain_mm_3d": 0, "rain_mm_7d": 0,
                "rain_prob_3d_pct": 0, "rain_prob_7d_pct": 0,
                "hot_days_7d": 0,
                "summary": "Weather data unavailable — assume neutral",
                "source": "mock",
            }

    # ---------- decision tree ----------
    def _decide(self, state: dict, weather: dict, shelf: dict, festival: Optional[dict]) -> tuple[str, str]:
        """Primary action. MSP is handled separately as an advisory note, not
        as a hard re-routing, because govt procurement is quota-limited and
        paperwork-heavy — not a realistic default for most farmers.
        """
        moisture = state.get("moisture", 12.0)
        grade    = state.get("grade", "B").upper()
        trend    = state.get("trend", "stable")
        best     = state.get("best_market", {}) or {}
        net      = best.get("net_price_per_q", 0)

        # 1. URGENT_SELL — spoilage risk
        if moisture > 14 or weather["rain_prob_3d_pct"] >= 70 or weather["rain_mm_3d"] >= 25:
            return "URGENT_SELL", (
                f"Spoilage risk: moisture {moisture}% and "
                f"{weather['rain_mm_3d']}mm rain expected in next 3 days. "
                f"Sell at {best.get('market','nearest APMC')} immediately."
            )

        # 2. SELL_NOW — festival window + rising trend
        if festival and festival["days_away"] <= 7 and trend == "rising" and net > 0:
            return "SELL_NOW", (
                f"{festival['name']} in {festival['days_away']} days "
                f"(+{festival['spike_pct']}% demand spike) and prices rising. "
                f"Sell at {best.get('market','best APMC')} now to catch the festival premium."
            )

        # 3. WAIT — rising prices, clear weather, adequate shelf life
        if trend == "rising" and weather["rain_mm_7d"] < 20 and shelf["days"] >= 15:
            hint = ""
            if festival and festival["days_away"] <= 20:
                hint = f" {festival['name']} is also {festival['days_away']} days away."
            return "WAIT", (
                f"Prices trending up, weather stays dry next week, and {shelf['days']}-day "
                f"shelf life gives you room.{hint} Hold for a better price."
            )

        # 4. HOLD_CAUTION — grade C, consider re-cleaning
        if grade == "C":
            return "HOLD_CAUTION", (
                "Grade C produce. If possible, re-clean or re-grade before selling; "
                "otherwise expect discounted prices at APMC."
            )

        # 5. Default — sell at best market
        return "SELL_NOW", (
            f"Sell Grade {grade} {state.get('millet','grain').title()} at "
            f"{best.get('market','best APMC')} for net ₹{net}/q."
        )

    def _msp_advisory(self, state: dict) -> Optional[dict]:
        """Return an advisory note if MSP > predicted net. Non-blocking — the
        farmer keeps the APMC recommendation but sees the govt alternative.
        """
        msp_check = state.get("msp_check") or {}
        if msp_check.get("status") != "BELOW_MSP":
            return None
        msp = msp_check.get("msp", 0)
        net = msp_check.get("your_best_net", 0)
        gap = msp - net
        qty = state.get("quantity_quintal", 1)
        return {
            "msp_per_quintal": msp,
            "your_best_net": net,
            "gap_per_quintal": round(gap, 2),
            "extra_total_if_govt": round(gap * qty, 2),
            "note": (
                f"Govt MSP for this millet is ₹{msp}/quintal — that's "
                f"₹{round(gap,2)} more per quintal than the best APMC net. "
                f"If you can access FCI / NAFED procurement (requires registration, "
                f"has quotas, and payment takes longer), you could earn roughly "
                f"₹{round(gap*qty,2)} more for your {qty} quintals. "
                f"Check eNAM portal or your local FCI centre for availability."
            ),
        }

    # ---------- cross-agent verification ----------
    def _verify(self, state: dict) -> tuple[str, str, list[str]]:
        """Cross-agent sanity checks. Flags only real anomalies — absolute
        price thresholds are not used because they depend on training-data era.
        """
        issues: list[str] = []
        q_conf = state.get("quality_score", 1.0)
        best = state.get("best_market", {}) or {}
        net = best.get("net_price_per_q", 0)
        apmc = best.get("apmc_price", 0)

        if q_conf < 0.5:
            issues.append(
                f"Quality model confidence low ({q_conf:.2f}) — manual grading recommended"
            )
        if apmc and net and net < 0.5 * apmc:
            issues.append(
                "Transport + commission eats >50% of gross at best market — "
                "consider a closer APMC or shared transport"
            )

        if q_conf < 0.5:
            return "SUSPICIOUS", "HIGH", issues
        if issues:
            return "SUSPICIOUS", "MEDIUM", issues
        return "VERIFIED", "LOW", issues

    # ---------- orchestrator entry ----------
    def predict(self, state: dict) -> dict:
        # Resolve lat/lon from Agent 3's farmer_location, fall back to state['location']
        farmer_loc = state.get("farmer_location") or {}
        lat = farmer_loc.get("lat") or (state.get("location") or {}).get("lat")
        lon = farmer_loc.get("lon") or (state.get("location") or {}).get("lng") or (state.get("location") or {}).get("lon")

        weather = self.fetch_weather(lat, lon) if lat and lon else {
            "rain_mm_3d": 0, "rain_mm_7d": 0,
            "rain_prob_3d_pct": 0, "rain_prob_7d_pct": 0,
            "hot_days_7d": 0,
            "summary": "No location — weather skipped",
            "source": "missing",
        }
        shelf = shelf_life_days(state.get("moisture", 12.0))
        festival = next_festival()
        action, reason = self._decide(state, weather, shelf, festival)
        status, risk, issues = self._verify(state)
        msp_advisory = self._msp_advisory(state)

        # Human-readable insight bullets
        insights = [reason, f"Shelf life: ~{shelf['days']} days ({shelf['note']})", f"Weather: {weather['summary']}"]
        if festival:
            insights.append(
                f"Next festival: {festival['name']} in {festival['days_away']} days "
                f"(+{festival['spike_pct']}% demand — {festival['reason']})"
            )
        # MSP note is surfaced separately in the UI; don't duplicate it here.
        if issues:
            insights.append("⚠️ " + "; ".join(issues))

        explanation = self._build_explanation(
            state, action, weather, shelf, festival
        )

        return {
            "action": action,
            "market": (state.get("best_market") or {}).get("market"),
            "reason": reason,
            "status": status,
            "risk": risk,
            "issues": issues,
            "shelf_life": shelf,
            "weather": weather,
            "next_festival": festival,
            "msp_advisory": msp_advisory,
            "decision_insights": insights,
            "explanation": explanation,
        }

    @staticmethod
    def _build_explanation(
        state: dict, action: str, weather: dict, shelf: dict, festival: Optional[dict]
    ) -> dict:
        """Generate a friendly Marathi + English paragraph summarizing the
        decision for the farmer. Pure templates — no LLM, no network call."""
        best = state.get("best_market") or {}
        millet_raw = str(state.get("millet") or "millet").lower()
        millet_mr = MILLET_MR.get(millet_raw, millet_raw)
        millet_en = millet_raw.title()
        grade = state.get("grade") or "B"
        qty = state.get("quantity_quintal") or 1
        market_name = best.get("market") or "the nearest APMC"
        distance = round(best.get("distance_km") or 0, 1)
        net_price = round(
            best.get("net_price_per_q") or state.get("expected_price") or 0, 2
        )
        total_revenue = round(
            best.get("total_net_revenue") or state.get("expected_total_revenue") or 0, 2
        )
        rain_mm = weather.get("rain_mm_3d", 0)
        shelf_days = shelf.get("days", "—")
        action_up = (action or "SELL_NOW").upper()
        action_en_word = ACTION_EN.get(action_up, "sell")
        action_mr_word = ACTION_MR.get(action_up, "विकणे")

        marathi = (
            f"शेतकरी साहेब, तुमची ग्रेड {grade} {millet_mr} ({qty} क्विंटल) "
            f"{market_name} येथे {action_mr_word} सर्वोत्तम आहे. "
            f"तुम्हाला सर्व खर्च वजा करून ₹{net_price}/क्विंटल मिळेल — एकूण ₹{total_revenue}. "
            f"पुढील ३ दिवसांत {rain_mm} मिमी पाऊस अपेक्षित आहे; "
            f"धान्य सुरक्षित ठेवण्याचा कालावधी {shelf_days} दिवस आहे."
        )
        english = (
            f"Sir, your Grade {grade} {millet_en} ({qty} quintals) is best to "
            f"{action_en_word} at {market_name} ({distance} km away). "
            f"Net price ₹{net_price}/quintal — total revenue ₹{total_revenue}. "
            f"Rain next 3 days: {rain_mm} mm. Storage life: {shelf_days} days."
        )
        if festival:
            festival_en = (
                f" Demand rises in {festival['days_away']} days for {festival['name']} "
                f"(+{festival['spike_pct']}%)."
            )
            festival_mr = (
                f" {festival['days_away']} दिवसांनी {festival['name']} सणासाठी मागणी "
                f"+{festival['spike_pct']}% वाढेल."
            )
            english += festival_en
            marathi += festival_mr
        return {"marathi": marathi, "english": english}
