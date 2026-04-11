"""MilletSaarthi — Streamlit UI.

Run with:
    streamlit run app/main.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Ensure project root on sys.path when Streamlit runs this file directly
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # must import before streamlit to avoid DLL conflict on Windows
import streamlit as st

from app.orchestrator import MilletSaarthiOrchestrator


# ==========================================================================
# TRANSLATIONS
# ==========================================================================
LANG = {
    "English": {
        "page_title": "MilletSaarthi — Smart Millet Selling Advisor",
        "sidebar_title": "🌾 Farmer Inputs",
        "upload_label": "Upload a clear photo of your grain",
        "location_label": "Your location (village, district, state)",
        "quantity_label": "Quantity (quintals)",
        "run_btn": "🚀 Get Recommendation",
        "main_title": "🌾 MilletSaarthi",
        "subtitle": "AI-powered selling advisor for millet farmers — Quality → Price → Market → Decision",
        "info_msg": "Upload a grain image, enter your location and quantity, and click **Get Recommendation** in the sidebar to run the full 4-agent pipeline.",
        "no_image": "Please upload a grain image before running.",
        "running": "Running the 4-agent pipeline...",
        "agent1_msg": "🔍 Agent 1 — classifying grain and grade",
        "agent2_msg": "💰 Agent 2 — predicting market price",
        "agent3_msg": "🗺️ Agent 3 — comparing nearby APMC markets",
        "agent4_msg": "🧠 Agent 4 — running decision rules + weather",
        "done": "Pipeline complete",
        "tab_dashboard": "🌾 Farmer Dashboard",
        "tab_analysis": "🔬 Analysis Flow (for mentor demo)",
        "recommendation": "Recommendation",
        "why": "Why",
        "market": "🏆 Market",
        "distance": "Distance",
        "transport": "Transport ₹/q",
        "net_profit": "Net profit",
        "verification": "Verification",
        "risk": "Risk",
        "flagged_issues": "⚠️ Flagged issues",
        "quality_header": "1 · Quality Assessment",
        "grain": "Grain",
        "grade": "Grade",
        "confidence": "Confidence",
        "source": "Source",
        "top3": "Top-3 predictions",
        "price_header": "2 · Price Prediction",
        "expected_price": "Expected ₹/quintal",
        "trend": "Trend",
        "total_revenue": "Total revenue",
        "model_confidence": "Model confidence",
        "price_range": "Price range (±5%)",
        "market_header": "3 · Market Comparison",
        "best_market": "🏆 Best market",
        "net_per_q": "Net ₹/quintal",
        "total_net_rev": "Total net revenue",
        "nearest": "📍 Nearest",
        "tbl_market": "Market", "tbl_district": "District", "tbl_dist": "Dist (km)",
        "tbl_apmc": "APMC ₹/q", "tbl_transport": "Transport ₹/q",
        "tbl_comm": "Comm ₹/q", "tbl_net": "Net ₹/q", "tbl_total": "Total Net ₹",
        "shared_transport": "🤝 **Shared transport opportunity:**",
        "market_insights": "📊 Market insights",
        "decision_header": "4 · Decision Advisor",
        "shelf_life": "Shelf life",
        "rain": "Rain next 3 days",
        "next_festival": "Next festival",
        "weather_outlook": "Weather outlook",
        "storage_note": "Storage note",
        "festival_driver": "Festival driver",
        "full_reasoning": "Full reasoning",
        "msp_alt": "💡 **Government MSP alternative:**",
        "your_grain": "Your grain",
        "days": "days",
        "language": "Language / भाषा",
        "actions": {"SELL_NOW": "SELL NOW", "URGENT_SELL": "URGENT SELL", "WAIT": "WAIT",
                    "HOLD_CAUTION": "HOLD (CAUTION)", "HUMAN_REVIEW": "HUMAN REVIEW", "ERROR": "ERROR"},
        "statuses": {"VERIFIED": "VERIFIED", "UNVERIFIED": "UNVERIFIED"},
        "risks": {"LOW": "LOW", "MEDIUM": "MEDIUM", "HIGH": "HIGH"},
        "trends": {"rising": "Rising", "falling": "Falling", "stable": "Stable"},
    },
    "हिंदी": {
        "page_title": "मिलेटसारथी — बाजरा बेचने का स्मार्ट सलाहकार",
        "sidebar_title": "🌾 किसान जानकारी",
        "upload_label": "अपने अनाज की साफ फोटो अपलोड करें",
        "location_label": "आपका स्थान (गांव, जिला, राज्य)",
        "quantity_label": "मात्रा (क्विंटल)",
        "run_btn": "🚀 सिफारिश पाएं",
        "main_title": "🌾 मिलेटसारथी",
        "subtitle": "बाजरा किसानों के लिए AI-संचालित बिक्री सलाहकार — गुणवत्ता → मूल्य → मंडी → निर्णय",
        "info_msg": "अनाज की फोटो अपलोड करें, अपना स्थान और मात्रा दर्ज करें, फिर साइडबार में **सिफारिश पाएं** पर क्लिक करें।",
        "no_image": "कृपया चलाने से पहले अनाज की फोटो अपलोड करें।",
        "running": "4-एजेंट पाइपलाइन चल रही है...",
        "agent1_msg": "🔍 एजेंट 1 — अनाज और ग्रेड की पहचान",
        "agent2_msg": "💰 एजेंट 2 — बाजार मूल्य का अनुमान",
        "agent3_msg": "🗺️ एजेंट 3 — नजदीकी APMC मंडियों की तुलना",
        "agent4_msg": "🧠 एजेंट 4 — निर्णय नियम और मौसम",
        "done": "पाइपलाइन पूरी हुई",
        "tab_dashboard": "🌾 किसान डैशबोर्ड",
        "tab_analysis": "🔬 विश्लेषण प्रवाह (मेंटर डेमो)",
        "recommendation": "सिफारिश",
        "why": "कारण",
        "market": "🏆 मंडी",
        "distance": "दूरी",
        "transport": "परिवहन ₹/क्वि",
        "net_profit": "शुद्ध लाभ",
        "verification": "सत्यापन",
        "risk": "जोखिम",
        "flagged_issues": "⚠️ चिन्हित समस्याएं",
        "quality_header": "1 · गुणवत्ता मूल्यांकन",
        "grain": "अनाज",
        "grade": "ग्रेड",
        "confidence": "विश्वास",
        "source": "स्रोत",
        "top3": "शीर्ष-3 अनुमान",
        "price_header": "2 · मूल्य अनुमान",
        "expected_price": "अपेक्षित ₹/क्विंटल",
        "trend": "रुझान",
        "total_revenue": "कुल आय",
        "model_confidence": "मॉडल विश्वास",
        "price_range": "मूल्य सीमा (±5%)",
        "market_header": "3 · मंडी तुलना",
        "best_market": "🏆 सर्वश्रेष्ठ मंडी",
        "net_per_q": "शुद्ध ₹/क्विंटल",
        "total_net_rev": "कुल शुद्ध आय",
        "nearest": "📍 निकटतम",
        "tbl_market": "मंडी", "tbl_district": "जिला", "tbl_dist": "दूरी (km)",
        "tbl_apmc": "APMC ₹/क्वि", "tbl_transport": "परिवहन ₹/क्वि",
        "tbl_comm": "कमीशन ₹/क्वि", "tbl_net": "शुद्ध ₹/क्वि", "tbl_total": "कुल शुद्ध ₹",
        "shared_transport": "🤝 **साझा परिवहन का अवसर:**",
        "market_insights": "📊 मंडी अंतर्दृष्टि",
        "decision_header": "4 · निर्णय सलाहकार",
        "shelf_life": "शेल्फ लाइफ",
        "rain": "अगले 3 दिन बारिश",
        "next_festival": "अगला त्योहार",
        "weather_outlook": "मौसम पूर्वानुमान",
        "storage_note": "भंडारण नोट",
        "festival_driver": "त्योहार प्रभाव",
        "full_reasoning": "पूर्ण तर्क",
        "msp_alt": "💡 **सरकारी MSP विकल्प:**",
        "your_grain": "आपका अनाज",
        "days": "दिन",
        "language": "Language / भाषा",
        "actions": {"SELL_NOW": "अभी बेचें", "URGENT_SELL": "तुरंत बेचें", "WAIT": "रुकें",
                    "HOLD_CAUTION": "सावधानी से रखें", "HUMAN_REVIEW": "मैन्युअल जांच", "ERROR": "त्रुटि"},
        "statuses": {"VERIFIED": "सत्यापित", "UNVERIFIED": "असत्यापित"},
        "risks": {"LOW": "कम", "MEDIUM": "मध्यम", "HIGH": "अधिक"},
        "trends": {"rising": "बढ़ रहा है", "falling": "गिर रहा है", "stable": "स्थिर"},
    },
    "मराठी": {
        "page_title": "मिलेटसारथी — ज्वारी विक्री स्मार्ट सल्लागार",
        "sidebar_title": "🌾 शेतकरी माहिती",
        "upload_label": "तुमच्या धान्याचा स्पष्ट फोटो अपलोड करा",
        "location_label": "तुमचे स्थान (गाव, जिल्हा, राज्य)",
        "quantity_label": "प्रमाण (क्विंटल)",
        "run_btn": "🚀 शिफारस मिळवा",
        "main_title": "🌾 मिलेटसारथी",
        "subtitle": "ज्वारी शेतकऱ्यांसाठी AI-चालित विक्री सल्लागार — गुणवत्ता → किंमत → बाजार → निर्णय",
        "info_msg": "धान्याचा फोटो अपलोड करा, तुमचे स्थान आणि प्रमाण टाका, नंतर साइडबारमध्ये **शिफारस मिळवा** वर क्लिक करा.",
        "no_image": "कृपया चालवण्यापूर्वी धान्याचा फोटो अपलोड करा.",
        "running": "4-एजंट पाइपलाइन चालू आहे...",
        "agent1_msg": "🔍 एजंट 1 — धान्य आणि ग्रेड ओळख",
        "agent2_msg": "💰 एजंट 2 — बाजारभाव अंदाज",
        "agent3_msg": "🗺️ एजंट 3 — जवळच्या APMC बाजारांची तुलना",
        "agent4_msg": "🧠 एजंट 4 — निर्णय नियम आणि हवामान",
        "done": "पाइपलाइन पूर्ण",
        "tab_dashboard": "🌾 शेतकरी डॅशबोर्ड",
        "tab_analysis": "🔬 विश्लेषण प्रवाह (मेंटर डेमो)",
        "recommendation": "शिफारस",
        "why": "कारण",
        "market": "🏆 बाजार",
        "distance": "अंतर",
        "transport": "वाहतूक ₹/क्वि",
        "net_profit": "निव्वळ नफा",
        "verification": "पडताळणी",
        "risk": "जोखीम",
        "flagged_issues": "⚠️ नोंदवलेल्या समस्या",
        "quality_header": "1 · गुणवत्ता मूल्यांकन",
        "grain": "धान्य",
        "grade": "ग्रेड",
        "confidence": "विश्वास",
        "source": "स्रोत",
        "top3": "शीर्ष-3 अंदाज",
        "price_header": "2 · किंमत अंदाज",
        "expected_price": "अपेक्षित ₹/क्विंटल",
        "trend": "कल",
        "total_revenue": "एकूण उत्पन्न",
        "model_confidence": "मॉडेल विश्वास",
        "price_range": "किंमत श्रेणी (±5%)",
        "market_header": "3 · बाजार तुलना",
        "best_market": "🏆 सर्वोत्तम बाजार",
        "net_per_q": "निव्वळ ₹/क्विंटल",
        "total_net_rev": "एकूण निव्वळ उत्पन्न",
        "nearest": "📍 जवळचा",
        "tbl_market": "बाजार", "tbl_district": "जिल्हा", "tbl_dist": "अंतर (km)",
        "tbl_apmc": "APMC ₹/क्वि", "tbl_transport": "वाहतूक ₹/क्वि",
        "tbl_comm": "कमिशन ₹/क्वि", "tbl_net": "निव्वळ ₹/क्वि", "tbl_total": "एकूण निव्वळ ₹",
        "shared_transport": "🤝 **सामायिक वाहतूक संधी:**",
        "market_insights": "📊 बाजार अंतर्दृष्टी",
        "decision_header": "4 · निर्णय सल्लागार",
        "shelf_life": "शेल्फ लाइफ",
        "rain": "पुढील 3 दिवस पाऊस",
        "next_festival": "पुढचा सण",
        "weather_outlook": "हवामान अंदाज",
        "storage_note": "साठवणूक टीप",
        "festival_driver": "सणाचा प्रभाव",
        "full_reasoning": "संपूर्ण तर्क",
        "msp_alt": "💡 **सरकारी MSP पर्याय:**",
        "your_grain": "तुमचे धान्य",
        "days": "दिवस",
        "language": "Language / भाषा",
        "actions": {"SELL_NOW": "आता विका", "URGENT_SELL": "तातडीने विका", "WAIT": "थांबा",
                    "HOLD_CAUTION": "सावधगिरीने ठेवा", "HUMAN_REVIEW": "मॅन्युअल तपासणी", "ERROR": "त्रुटी"},
        "statuses": {"VERIFIED": "सत्यापित", "UNVERIFIED": "असत्यापित"},
        "risks": {"LOW": "कमी", "MEDIUM": "मध्यम", "HIGH": "जास्त"},
        "trends": {"rising": "वाढत आहे", "falling": "घसरत आहे", "stable": "स्थिर"},
    },
}

# Language codes for googletrans
_LANG_CODE = {"English": "en", "हिंदी": "hi", "मराठी": "mr"}
_translate_cache: dict[tuple[str, str], str] = {}

def _tr(text: str, lang_key: str) -> str:
    """Translate text to the selected language. Returns original if English."""
    if lang_key == "English" or not text or not text.strip():
        return text
    dest = _LANG_CODE[lang_key]
    cache_key = (text, dest)
    if cache_key in _translate_cache:
        return _translate_cache[cache_key]
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest=dest)
        _translate_cache[cache_key] = result.text
        return result.text
    except Exception:
        return text


# --- Page setup ------------------------------------------------------------
st.set_page_config(
    page_title="MilletSaarthi — Smart Millet Selling Advisor",
    page_icon="🌾",
    layout="wide",
)


@st.cache_resource
def get_orchestrator() -> MilletSaarthiOrchestrator:
    return MilletSaarthiOrchestrator()


# --- Language selector (top of sidebar) ------------------------------------
lang_choice = st.sidebar.selectbox("Language / भाषा", list(LANG.keys()))
T = LANG[lang_choice]


# --- Sidebar: inputs -------------------------------------------------------
st.sidebar.title(T["sidebar_title"])

image_file = st.sidebar.file_uploader(
    T["upload_label"],
    type=["jpg", "jpeg", "png"],
)

location_text = st.sidebar.text_input(
    T["location_label"],
    value="Baramati, Maharashtra",
)

quantity = st.sidebar.number_input(
    T["quantity_label"], min_value=0.5, max_value=500.0, value=10.0, step=0.5
)

# Sensible defaults — not exposed to the farmer
moisture = 12.0
max_distance = 300

run_btn = st.sidebar.button(
    T["run_btn"], type="primary", use_container_width=True
)


# --- Header ----------------------------------------------------------------
st.title(T["main_title"])
st.caption(T["subtitle"])

if not run_btn:
    st.info(T["info_msg"])
    st.stop()

if image_file is None:
    st.error(T["no_image"])
    st.stop()


# --- Save upload to temp file ---------------------------------------------
# Use getvalue() — it does NOT consume the buffer, so we can reuse the bytes
# for st.image rendering after the orchestrator finishes.
image_bytes = image_file.getvalue()
suffix = Path(image_file.name).suffix or ".jpg"
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    tmp.write(image_bytes)
    tmp_path = tmp.name


# --- Run pipeline ----------------------------------------------------------
with st.status(T["running"], expanded=True) as status:
    orch = get_orchestrator()
    st.write(T["agent1_msg"])
    st.write(T["agent2_msg"])
    st.write(T["agent3_msg"])
    st.write(T["agent4_msg"])
    result = orch.run(
        image_path=tmp_path,
        location_text=location_text,
        quantity_quintal=quantity,
        moisture=moisture,
        max_distance_km=max_distance,
    )
    status.update(label=T["done"], state="complete", expanded=False)


# ==========================================================================
# TABS
# ==========================================================================
tab_dashboard, tab_analysis = st.tabs(
    [T["tab_dashboard"], T["tab_analysis"]]
)


# ==========================================================================
# TAB 1 — FARMER DASHBOARD
# ==========================================================================
with tab_dashboard:
    # --- Top: recommendation banner ---------------------------------------
    action = result.get("action", "UNKNOWN")
    action_display = T.get("actions", {}).get(action, action)
    action_style = {
        "SELL_NOW":     ("✅", "success"),
        "URGENT_SELL":  ("⚠️", "error"),
        "WAIT":         ("⏳", "info"),
        "HOLD_CAUTION": ("⚠️", "warning"),
        "HUMAN_REVIEW": ("🧑‍🌾", "warning"),
        "ERROR":        ("❌", "error"),
    }.get(action, ("ℹ️", "info"))
    icon, kind = action_style

    # Translate dynamic values
    raw_status = result.get("status", "-")
    raw_risk = result.get("risk", "-")
    raw_trend = result.get("trend", "-")
    disp_status = T.get("statuses", {}).get(raw_status, raw_status)
    disp_risk = T.get("risks", {}).get(raw_risk, raw_risk)
    disp_trend = T.get("trends", {}).get(raw_trend.lower(), raw_trend).title()

    col_img, col_reco = st.columns([1, 2], gap="large")
    with col_img:
        st.image(image_bytes, caption=T["your_grain"], width=320)
    with col_reco:
        getattr(st, kind)(f"{icon}  **{T['recommendation']}: {action_display}**")
        st.markdown(f"**{T['why']}:** {_tr(result.get('reason','(no reason)'), lang_choice)}")

        _best = result.get("best_market") or {}
        if _best:
            b1, b2, b3, b4 = st.columns(4)
            b1.metric(T["market"], _best.get("market", "-"))
            b2.metric(T["distance"], f"{_best.get('distance_km', 0)} km")
            b3.metric(T["transport"], f"₹{_best.get('transport_per_q', 0):,.0f}")
            b4.metric(
                T["net_profit"],
                f"₹{_best.get('total_net_revenue', 0):,.0f}",
                delta=f"₹{_best.get('net_price_per_q', 0):,.0f}/q",
            )

        st.markdown(
            f"**{T['verification']}:** {disp_status} • "
            f"**{T['risk']}:** **{disp_risk}**"
        )
        if result.get("issues"):
            with st.expander(T["flagged_issues"], expanded=True):
                for i in result["issues"]:
                    st.markdown(f"- {i}")

    st.divider()

    # --- Agent 1: Quality --------------------------------------------------
    st.header(T["quality_header"])
    if result.get("invalid_image"):
        st.error(f"**{result.get('error', 'Invalid image uploaded.')}**")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["grain"], result.get("millet", "?").title())
        c2.metric(T["grade"], result.get("grade", "?"))
        c3.metric(T["confidence"], f"{result.get('quality_score',0)*100:.1f}%")
        c4.metric(T["source"], result.get("quality_source", "-"))
    if result.get("top3"):
        with st.expander(T["top3"]):
            for t in result["top3"]:
                st.progress(t["prob"], text=f"{t['class']} — {t['prob']*100:.1f}%")

    # --- Agent 2: Price ----------------------------------------------------
    st.header(T["price_header"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T["expected_price"], f"₹{result.get('expected_price',0):,.0f}")
    c2.metric(T["trend"], disp_trend)
    c3.metric(T["total_revenue"], f"₹{result.get('expected_total_revenue',0):,.0f}")
    c4.metric(T["model_confidence"], f"{result.get('confidence',0)*100:.0f}%")
    pr = result.get("price_range")
    if pr:
        st.caption(f"{T['price_range']}: ₹{pr[0]:,.0f} – ₹{pr[1]:,.0f}")

    # --- Agent 3: Market ---------------------------------------------------
    st.header(T["market_header"])
    best = result.get("best_market") or {}
    local = result.get("local_market") or {}
    msp_check = result.get("msp_check") or {}

    if best:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["best_market"], best.get("market", "-"))
        c2.metric(T["net_per_q"], f"₹{best.get('net_price_per_q',0):,.0f}")
        c3.metric(T["distance"], f"{best.get('distance_km',0)} km")
        c4.metric(T["total_net_rev"], f"₹{best.get('total_net_revenue',0):,.0f}")

    if local and local.get("market") != best.get("market"):
        st.caption(
            f"{T['nearest']}: **{local.get('market')}** "
            f"({local.get('distance_km',0)} km) — ₹{local.get('net_price_per_q',0):,.0f}/q"
        )

    top5 = result.get("top_5_nearest") or []
    if top5:
        import pandas as pd
        df = pd.DataFrame(top5)[[
            "market", "district", "distance_km", "apmc_price",
            "transport_per_q", "commission_per_q", "net_price_per_q", "total_net_revenue",
        ]]
        df = df.rename(columns={
            "market": T["tbl_market"], "district": T["tbl_district"],
            "distance_km": T["tbl_dist"], "apmc_price": T["tbl_apmc"],
            "transport_per_q": T["tbl_transport"], "commission_per_q": T["tbl_comm"],
            "net_price_per_q": T["tbl_net"], "total_net_revenue": T["tbl_total"],
        })
        # Format distance to 1 decimal
        df[T["tbl_dist"]] = df[T["tbl_dist"]].apply(lambda x: f"{x:.1f}")
        for col in [T["tbl_apmc"], T["tbl_transport"], T["tbl_comm"], T["tbl_net"], T["tbl_total"]]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"₹{x:,.0f}")
        st.table(df.reset_index(drop=True))

    shared = result.get("shared_transport_opportunity")
    if shared:
        st.info(f"{T['shared_transport']} {_tr(shared.get('message',''), lang_choice)}")

    m_insights = result.get("market_insights") or []
    if m_insights:
        with st.expander(T["market_insights"], expanded=True):
            for i in m_insights:
                st.markdown(f"- {_tr(i, lang_choice)}")

    # --- Agent 4: Decision details -----------------------------------------
    st.header(T["decision_header"])
    c1, c2, c3 = st.columns(3)
    shelf = result.get("shelf_life") or {}
    weather = result.get("weather") or {}
    fest = result.get("next_festival")

    c1.metric(T["shelf_life"], f"{shelf.get('days','-')} {T['days']}")
    c2.metric(T["rain"], f"{weather.get('rain_mm_3d',0)} mm")
    c3.metric(
        T["next_festival"],
        f"{fest['name']} ({fest['days_away']}d)" if fest else "—",
    )

    st.markdown(f"**{T['weather_outlook']}:** {_tr(weather.get('summary','-'), lang_choice)}")
    if shelf.get("note"):
        st.markdown(f"**{T['storage_note']}:** {_tr(shelf['note'], lang_choice)}")
    if fest:
        st.markdown(
            f"**{T['festival_driver']}:** {fest['name']} — {fest['days_away']} {T['days']} — "
            f"+{fest['spike_pct']}% ({_tr(fest['reason'], lang_choice)})"
        )

    decision_insights = result.get("decision_insights") or []
    if decision_insights:
        st.subheader(T["full_reasoning"])
        for i in decision_insights:
            st.markdown(f"- {_tr(i, lang_choice)}")

    msp_adv = result.get("msp_advisory")
    if msp_adv:
        msp_msg = (
            f"MSP = ₹{msp_adv['msp_per_quintal']}/q, "
            f"₹{msp_adv['gap_per_quintal']} more than APMC net ₹{msp_adv['your_best_net']}/q. "
            f"₹{msp_adv['extra_total_if_govt']} extra for {result.get('quantity_quintal', '?')}q. "
            f"Check eNAM / FCI."
        )
        st.info(f"{T['msp_alt']} {_tr(msp_msg, lang_choice)}")


# ==========================================================================
# TAB 2 — ANALYSIS FLOW (FOR MENTOR DEMO)
# ==========================================================================
with tab_analysis:
    st.markdown(
        "### End-to-end agentic flow\n"
        "This view shows **exactly** how the farmer's request moved through "
        "the system: the orchestrator's planner decisions, every message "
        "passed between agents, and the actual model outputs at each step. "
        "Use this to demonstrate dynamic routing and multi-agent reasoning."
    )

    trace = result.get("agentic_trace", [])
    pipeline = result.get("pipeline", [])

    # ---- Step 0: Farmer input card ---------------------------------------
    with st.container():
        st.markdown("---")
        st.markdown("#### 📥 Step 0 — Farmer Input")
        ic1, ic2 = st.columns([1, 2])
        with ic1:
            st.image(image_bytes, caption="Uploaded grain", width=320)
        with ic2:
            st.markdown(
                f"- **Location text:** `{location_text}`\n"
                f"- **Quantity:** `{quantity}` quintals\n"
                f"- **Moisture (default):** `{moisture}%`\n"
                f"- **Month:** `{result.get('year')}-{result.get('month'):02d}`"
            )
            st.caption(
                "These four fields are the *only* inputs the farmer provides. "
                "Everything else is derived by the agents."
            )

    st.markdown("#### ⬇️ Orchestrator receives request → invokes Planner")

    # ---- Build a lookup: per-iteration state snapshot --------------------
    # For each iteration, show (a) planner decision, (b) each agent that ran
    # and its actual output pulled from the final state.

    # Agent-name -> which state keys belong to its output (for the demo card)
    AGENT_OUTPUT_KEYS = {
        "quality": ["millet", "grade", "quality_score", "confidence", "top3", "quality_source"],
        "geocode": ["farmer_state", "farmer_district", "farmer_location"],
        "market": ["best_market", "local_market", "top_5_nearest", "msp_check",
                   "shared_transport_opportunity", "market_insights", "markets_evaluated",
                   "query_month"],
        "weather": ["weather"],
        "price": ["expected_price", "price_range", "trend", "expected_total_revenue",
                  "confidence", "price_source"],
        "decision": ["action", "reason", "status", "risk", "issues", "shelf_life",
                     "next_festival", "msp_advisory", "decision_insights"],
        "quality_retry": ["retry_image_path", "reflection_retries", "reflection_note"],
        "human_review": ["action", "reason", "status", "risk", "issues", "decision_insights"],
    }

    AGENT_ROLE = {
        "quality":       ("🔍 Agent 1", "Quality Assessment", "MobileNetV3 CNN"),
        "geocode":       ("📍 Tool",    "Geocoding",         "Nominatim OSM"),
        "market":        ("🗺️ Agent 3", "Market Comparison",  "XGBoost + OSRM"),
        "weather":       ("🌦️ Tool",    "Weather Forecast",  "Open-Meteo API"),
        "price":         ("💰 Agent 2", "Price Prediction",  "XGBoost regressor"),
        "decision":      ("🧠 Agent 4", "Decision Advisor",  "Rule engine"),
        "quality_retry": ("🔄 Agent 1", "Reflection Retry",  "PIL-enhanced image"),
        "human_review":  ("🧑‍🌾 Halt",  "Human Review",      "Pipeline short-circuit"),
    }

    def _extract_output(agent_name: str, state: dict) -> dict:
        keys = AGENT_OUTPUT_KEYS.get(agent_name, [])
        return {k: state[k] for k in keys if k in state}

    def _short_msg(agent_name: str, state: dict) -> str:
        """One-line human summary of what the agent 'told' the orchestrator."""
        if agent_name == "quality":
            m = state.get("millet", "?").title()
            g = state.get("grade", "?")
            c = state.get("quality_score", 0) * 100
            return f"→ Orchestrator: *This is **{m} Grade {g}**, confidence {c:.1f}%.*"
        if agent_name == "geocode":
            fl = state.get("farmer_location") or {}
            return (
                f"→ Orchestrator: *Resolved to **{fl.get('district','?')}, "
                f"{fl.get('state','?')}** (lat {fl.get('lat','?')}, lon {fl.get('lon','?')}).*"
            )
        if agent_name == "market":
            b = state.get("best_market") or {}
            n = state.get("markets_evaluated", 0)
            return (
                f"→ Orchestrator: *Evaluated {n} APMCs. Best = **{b.get('market','?')}** "
                f"at ₹{b.get('net_price_per_q',0):,.0f}/q net ({b.get('distance_km','?')} km).*"
            )
        if agent_name == "weather":
            w = state.get("weather") or {}
            return f"→ Orchestrator: *{w.get('summary','-')}*"
        if agent_name == "price":
            return (
                f"→ Orchestrator: *Baseline ₹{state.get('expected_price',0):,.0f}/q, "
                f"trend **{state.get('trend','?')}**.*"
            )
        if agent_name == "decision":
            return (
                f"→ Farmer: *Recommendation **{state.get('action','?')}** — "
                f"{state.get('reason','')}*"
            )
        if agent_name == "quality_retry":
            return (
                f"→ Orchestrator: *Re-ran on enhanced image, "
                f"{state.get('reflection_note','confidence updated')}.*"
            )
        if agent_name == "human_review":
            return "→ Farmer: *Image unclear — retake photo and try again.*"
        return ""

    # ---- Render each iteration as a card ---------------------------------
    for step in trace:
        iter_num = step.get("iter", 0)
        tasks = step.get("tasks") or []
        reason = step.get("reason", "")
        dur = step.get("duration_ms")
        action_label = step.get("action", "")

        if action_label == "done":
            st.markdown("---")
            with st.container():
                st.success(f"✅ **Iteration {iter_num} — Planner says: DONE.** {reason}")
            continue

        st.markdown("---")
        with st.container():
            # Planner header
            st.markdown(f"#### 🧭 Iteration {iter_num} — Planner decision")
            st.markdown(f"**🗣️ Planner:** *{reason}*")
            parallel = len(tasks) > 1
            if parallel:
                st.markdown(
                    f"**📤 Dispatches `{' + '.join(tasks)}` IN PARALLEL** "
                    f"(total wall-clock: {dur} ms)"
                )
            else:
                st.markdown(f"**📤 Dispatches `{tasks[0]}`** *({dur} ms)*")

            # Per-agent cards
            agent_cols = st.columns(len(tasks))
            for col, name in zip(agent_cols, tasks):
                badge, role, tech = AGENT_ROLE.get(name, ("🔧", name, "-"))
                # Find pipeline status for this invocation (last matching entry)
                pipe_hits = [p for p in pipeline if p.get("agent") == name]
                status = pipe_hits[-1]["status"] if pipe_hits else "?"
                status_icon = "✅" if status == "ok" else "❌"
                err = pipe_hits[-1].get("error") if pipe_hits else None

                with col:
                    st.markdown(f"**{badge} — {role}**")
                    st.caption(f"Tech: {tech}")
                    st.markdown(f"Status: {status_icon} `{status}`")
                    if err:
                        st.error(f"Error: {err}")
                    else:
                        # Message back to orchestrator
                        msg = _short_msg(name, result)
                        if msg:
                            st.markdown(msg)
                        # Expandable: full agent output JSON
                        out = _extract_output(name, result)
                        if out:
                            with st.expander("📄 Full agent output"):
                                st.json(out)

    # ---- Final decision card ---------------------------------------------
    st.markdown("#### 🎯 Final output delivered to farmer")
    with st.container():
        st.markdown("---")
        fc1, fc2 = st.columns([1, 2])
        with fc1:
            st.image(image_bytes, caption="Input", width=320)
        with fc2:
            st.markdown(f"### {icon} {result.get('action','-')}")
            st.markdown(f"**Reason:** {result.get('reason','-')}")
            if best:
                st.markdown(
                    f"**Market:** {best.get('market','-')} "
                    f"({best.get('distance_km','-')} km)"
                )
                st.markdown(
                    f"**Net price:** ₹{best.get('net_price_per_q',0):,.0f}/q × "
                    f"{quantity} quintals = "
                    f"**₹{best.get('total_net_revenue',0):,.0f}**"
                )
            st.markdown(
                f"**Verification:** {result.get('status','-')} • "
                f"Risk: {result.get('risk','-')}"
            )

    # ---- Low-level execution log & raw state -----------------------------
    with st.expander("🔧 Per-agent execution log"):
        for step in pipeline:
            icn = "✅" if step["status"] == "ok" else "❌"
            line = f"{icn} **{step['agent']}** — {step['status']}"
            if step.get("error"):
                line += f" ({step['error']})"
            st.markdown(line)

    with st.expander("📄 Raw final state JSON"):
        st.json(result)
