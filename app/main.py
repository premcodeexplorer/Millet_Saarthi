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

if sys.platform == "win32":
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
        "weather_msg": "🌦️ Weather tool — fetching 7-day forecast",
        "agent4_msg": "🧠 Agent 4 — fusing all signals into final recommendation",
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
        "explainer_header": "📢 Farmer's Recommendation (Marathi + English)",
        "explainer_marathi": "मराठीत",
        "explainer_english": "In English",
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
        "weather_msg": "🌦️ मौसम — 7-दिवसीय पूर्वानुमान प्राप्त कर रहे हैं",
        "agent4_msg": "🧠 एजेंट 4 — सभी संकेतों से अंतिम सिफारिश तैयार",
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
        "explainer_header": "📢 किसान के लिए सिफारिश (मराठी + अंग्रेज़ी)",
        "explainer_marathi": "मराठी में",
        "explainer_english": "अंग्रेज़ी में",
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
        "weather_msg": "🌦️ हवामान साधन — 7 दिवसांचा अंदाज मिळवत आहे",
        "agent4_msg": "🧠 एजंट 4 — सर्व माहितीतून अंतिम शिफारस",
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
        "explainer_header": "📢 शेतकऱ्यांसाठी शिफारस (मराठी + इंग्रजी)",
        "explainer_marathi": "मराठीत",
        "explainer_english": "इंग्रजीत",
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

# Language codes for the translation backend
_LANG_CODE = {"English": "en", "हिंदी": "hi", "मराठी": "mr"}
_translate_cache: dict[tuple[str, str], str] = {}

# Hand-curated translations for the most common templated strings produced by
# the agents. Checked first in _tr() before falling back to deep-translator.
# Guarantees the right wording for these strings even if the network call fails
# and avoids 30+ live API calls on first page render.
_MANUAL_TR: dict[str, dict[str, str]] = {
    "मराठी": {
        # Millet names (used as standalone metric values)
        "Bajra": "बाजरी",
        "Jowar": "ज्वारी",
        "Ragi": "नाचणी",
        "bajra": "बाजरी",
        "jowar": "ज्वारी",
        "ragi": "नाचणी",
        # Quality source labels
        "model": "मॉडेल",
        "image": "प्रतिमा",
        # Top-3 quality classes
        "Bajra Grade A": "बाजरी ग्रेड A", "Bajra Grade B": "बाजरी ग्रेड B",
        "Jowar Grade A": "ज्वारी ग्रेड A", "Jowar Grade B": "ज्वारी ग्रेड B", "Jowar Grade C": "ज्वारी ग्रेड C",
        "Ragi Grade A": "नाचणी ग्रेड A", "Ragi Grade B": "नाचणी ग्रेड B",
        # Shelf life notes (static — exact match)
        "Dry grain — safe for long storage": "कोरडे धान्य — दीर्घ साठवणीसाठी सुरक्षित",
        "Borderline — safe for 2-3 weeks": "मर्यादित आर्द्रता — २-३ आठवडे सुरक्षित",
        "High moisture — urgent, spoilage risk": "जास्त आर्द्रता — तातडीने विका, खराब होण्याचा धोका",
        "High moisture — very short shelf life": "जास्त आर्द्रता — अत्यंत कमी साठवणूक काळ",
        # Static weather summaries
        "Clear and dry for the next week": "पुढील आठवडा स्वच्छ आणि कोरडा",
        "Weather data unavailable — assume neutral": "हवामान माहिती उपलब्ध नाही — सामान्य गृहीत",
        "No location — weather skipped": "स्थान नाही — हवामान वगळले",
        # Festival reasons (static — from FESTIVALS table)
        "Til-gud laddoo + bajra bhakri demand": "तिळगूळ लाडू + बाजरी भाकरीची मागणी",
        "Puran poli and sweet preparations": "पुरणपोळी आणि गोड पदार्थ",
        "Marathi new year — sweet rotis": "मराठी नववर्ष — गोड पोळ्या",
        "Community bhandaras": "सामूहिक भंडारे",
        "Vari pilgrimage — bajra/jowar bhakri staple": "वारी यात्रा — बाजरी/ज्वारी भाकरी मुख्य अन्न",
        "10-day festival + modak preparations": "१०-दिवसांचा सण + मोदक तयारी",
        "Fasting foods (ragi, bajra prominent)": "उपवासाचे अन्न (नाचणी, बाजरी प्रमुख)",
        "Festive feasts": "सणाचे भोजन",
        "Peak festive demand — sweets and snacks": "सणाची सर्वोच्च मागणी — मिठाई आणि नाश्ता",
        "Winter festive baking": "हिवाळी सणाचे भाजणे",
        # Common phrase
        "Safe to sell.": "विकणे सुरक्षित.",
    },
    "हिंदी": {
        "Bajra": "बाजरा", "Jowar": "ज्वार", "Ragi": "रागी",
        "bajra": "बाजरा", "jowar": "ज्वार", "ragi": "रागी",
        "model": "मॉडल", "image": "तस्वीर",
        "Bajra Grade A": "बाजरा ग्रेड A", "Bajra Grade B": "बाजरा ग्रेड B",
        "Jowar Grade A": "ज्वार ग्रेड A", "Jowar Grade B": "ज्वार ग्रेड B", "Jowar Grade C": "ज्वार ग्रेड C",
        "Ragi Grade A": "रागी ग्रेड A", "Ragi Grade B": "रागी ग्रेड B",
        "Dry grain — safe for long storage": "सूखा अनाज — लंबे भंडारण के लिए सुरक्षित",
        "Borderline — safe for 2-3 weeks": "सीमित नमी — 2-3 हफ्ते सुरक्षित",
        "High moisture — urgent, spoilage risk": "अधिक नमी — तुरंत बेचें, खराब होने का खतरा",
        "High moisture — very short shelf life": "अधिक नमी — बहुत कम भंडारण अवधि",
        "Clear and dry for the next week": "अगले हफ्ते मौसम साफ और सूखा रहेगा",
        "Weather data unavailable — assume neutral": "मौसम डेटा उपलब्ध नहीं — सामान्य मानें",
        "No location — weather skipped": "स्थान नहीं — मौसम छोड़ दिया गया",
        "Til-gud laddoo + bajra bhakri demand": "तिल-गुड़ लड्डू + बाजरा रोटी की मांग",
        "Puran poli and sweet preparations": "पूरन पोली और मिठाई की तैयारी",
        "Marathi new year — sweet rotis": "मराठी नववर्ष — मीठी रोटी",
        "Community bhandaras": "सामुदायिक भंडारे",
        "Vari pilgrimage — bajra/jowar bhakri staple": "वारी तीर्थयात्रा — बाजरा/ज्वार रोटी मुख्य आहार",
        "10-day festival + modak preparations": "10 दिन का त्योहार + मोदक तैयारी",
        "Fasting foods (ragi, bajra prominent)": "व्रत के भोजन (रागी, बाजरा प्रमुख)",
        "Festive feasts": "त्योहारी भोज",
        "Peak festive demand — sweets and snacks": "त्योहारी मांग चरम पर — मिठाई और स्नैक्स",
        "Winter festive baking": "सर्दी की त्योहारी पकाई",
        "Safe to sell.": "बेचना सुरक्षित।",
    },
}

def _tr(text: str, lang_key: str) -> str:
    """Translate text to the selected language. Returns original on failure.

    Uses deep-translator (stable Google Translate wrapper). googletrans is
    notoriously broken — Google blocks it intermittently and it silently
    falls back to English, which is why Marathi mode used to leak English
    everywhere.
    """
    if lang_key == "English" or not text or not text.strip():
        return text
    # 1. Check the hand-curated overrides first (free, instant, guaranteed correct)
    manual = _MANUAL_TR.get(lang_key, {}).get(text.strip())
    if manual:
        return manual
    dest = _LANG_CODE[lang_key]
    cache_key = (text, dest)
    if cache_key in _translate_cache:
        return _translate_cache[cache_key]
    # 2. Fall back to deep-translator for novel / templated strings
    try:
        from deep_translator import GoogleTranslator
        result = GoogleTranslator(source="en", target=dest).translate(text)
        if result:
            _translate_cache[cache_key] = result
            return result
        return text
    except Exception:
        return text


# --- Page setup ------------------------------------------------------------
st.set_page_config(
    page_title="MilletSaarthi — Smart Millet Selling Advisor",
    page_icon="🌾",
    layout="wide",
)


# --- Custom CSS (pills, cards, mobile) -------------------------------------
st.markdown(
    """
<style>
/* Palette: primary olive #546B41 · cream #FFF8EC · tan #DCCCAC · text #333 */

/* Traffic-light decision cards — match warm cream/olive theme */
.ms-card {
    border-radius: 10px;
    padding: 16px 18px;
    margin: 4px 0;
    background: #FFFCF4;
    box-shadow: 0 1px 2px rgba(86, 64, 32, 0.06);
}
.ms-card-green { border-left: 5px solid #546B41; }   /* primary olive */
.ms-card-amber { border-left: 5px solid #B8860B; }   /* warm goldenrod */
.ms-card-red   { border-left: 5px solid #A33D2C; }   /* terracotta */
.ms-card-title {
    font-size: 14px;
    font-weight: 700;
    color: #3A3A3A;
    margin-bottom: 4px;
}
.ms-card-value { font-size: 22px; font-weight: 600; color: #333333; line-height: 1.2; }
.ms-card-sub   { font-size: 12px; color: #5C5C5C; margin-top: 6px; }

/* Big revenue number — uses primary olive instead of bright generic green */
.ms-revenue-label { font-size: 14px; color: #5C5C5C; }
.ms-revenue-value {
    font-size: 36px;
    font-weight: 700;
    color: #546B41;
    line-height: 1.2;
    margin-top: -4px;
}

/* Bilingual subtitle helper */
.ms-en-sub { font-size: 11px; color: #8A8A8A; font-weight: 400; margin-top: -6px; }

/* Reasoning bullet lines — slightly larger so they're easier to read */
.ms-reason {
    font-size: 15.5px;
    color: #3A3A3A;
    line-height: 1.75;
    margin: 4px 0;
}
.ms-reason b { color: #1f2937; }

/* Farmer-facing recommendation BOX — primary call-out at top of dashboard */
.ms-reco-box {
    background: #FAF3E0;                     /* slightly darker cream */
    border: 1px solid #DCCCAC;               /* secondary palette tan */
    border-left: 6px solid #546B41;          /* primary olive emphasis */
    border-radius: 10px;
    padding: 16px 22px;
    margin: 6px 0 18px 0;
    color: #333333;
}
.ms-reco-box .ms-reco-title {
    font-size: 16px;
    font-weight: 700;
    color: #3A3A3A;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.ms-reco-box .ms-reco-text {
    font-size: 16px;
    line-height: 1.6;
    color: #2F2F2F;
}

/* Native Streamlit bordered containers — make them match the recommendation
   box (cream background + olive left border). We only use bordered containers
   for the price-chart wrapper, so this single rule is safe. */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FAF3E0 !important;
    border: 1px solid #DCCCAC !important;
    border-left: 6px solid #546B41 !important;
    border-radius: 10px !important;
}

/* Mobile responsive — stack columns below 768px */
@media (max-width: 768px) {
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 0 100% !important;
        min-width: unset !important;
    }
    .ms-pill { display: block; margin: 4px 0; text-align: center; }
    .ms-revenue-value { font-size: 28px; }
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_orchestrator() -> MilletSaarthiOrchestrator:
    return MilletSaarthiOrchestrator()


@st.cache_data
def get_price_history():
    """Load master_prices.csv once for sparkline lookups."""
    import pandas as pd
    from app.config import PRICE_HISTORY_PATH
    return pd.read_csv(PRICE_HISTORY_PATH)


def _weather_risk(weather: dict) -> tuple[str, str, str]:
    """Return (level, marathi_label, color_class) based on rain in next 3 days.

    Thresholds: <5mm safe (green), 5-20mm caution (amber), >20mm risk (red).
    """
    rain_3d = weather.get("rain_mm_3d", 0) or 0
    if rain_3d > 20:
        return ("danger", "धोका", "red")
    if rain_3d >= 5:
        return ("caution", "सावधान", "amber")
    return ("safe", "सुरक्षित", "green")


# --- Language selectors (header + sidebar, kept in sync via session state)
LANGS = list(LANG.keys())
if "app_lang" not in st.session_state:
    st.session_state.app_lang = "मराठी"

# Sidebar selector (always visible per layout constraint)
sb_lang = st.sidebar.selectbox(
    "Language / भाषा",
    LANGS,
    index=LANGS.index(st.session_state.app_lang),
    key="sidebar_lang_widget",
)
if sb_lang != st.session_state.app_lang:
    st.session_state.app_lang = sb_lang
    st.rerun()

lang_choice = st.session_state.app_lang
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
# Language selector lives only in the sidebar (per layout constraint).
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
    st.write(T["weather_msg"])
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
    # --- Top: farmer recommendation (single language, boxed) --------------
    # Shows the recommendation in the language currently selected — this is
    # the final answer the farmer reads first, so it gets the prominent
    # cream-and-olive call-out box that matches the app theme.
    _explanation_top = result.get("explanation") or {}
    if _explanation_top:
        if lang_choice == "मराठी":
            _reco_text = _explanation_top.get("marathi", "—")
        elif lang_choice == "English":
            _reco_text = _explanation_top.get("english", "—")
        else:
            # Hindi: translate the English summary on the fly via deep-translator
            _reco_text = _tr(_explanation_top.get("english", "—"), lang_choice)

        st.markdown(
            f"<div class='ms-reco-box'>"
            f"<div class='ms-reco-title'>📢 {T['explainer_header'].replace('📢 ', '').split(' (')[0]}</div>"
            f"<div class='ms-reco-text'>{_reco_text}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.divider()

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
            # 2x2 metric grid (instead of 4 narrow columns) so longer market
            # names like "पुणे एपीएमसी" or "Ahmednagar APMC" don't truncate.
            b1, b2 = st.columns(2)
            b1.metric(T["market"], _tr(_best.get("market", "-"), lang_choice))
            b2.metric(
                T["net_profit"],
                f"₹{_best.get('total_net_revenue', 0):,.0f}",
                delta=f"₹{_best.get('net_price_per_q', 0):,.0f}/q",
            )
            b3, b4 = st.columns(2)
            b3.metric(T["distance"], f"{_best.get('distance_km', 0)} km")
            b4.metric(T["transport"], f"₹{_best.get('transport_per_q', 0):,.0f}")

        st.markdown(
            f"**{T['verification']}:** {disp_status} • "
            f"**{T['risk']}:** **{disp_risk}**"
        )
        if result.get("issues"):
            with st.expander(T["flagged_issues"], expanded=True):
                for i in result["issues"]:
                    st.markdown(f"- {_tr(i, lang_choice)}")

    st.divider()

    # --- Agent 1: Quality --------------------------------------------------
    st.header(T["quality_header"])
    if result.get("invalid_image"):
        st.error(f"**{result.get('error', 'Invalid image uploaded.')}**")
    else:
        # 3 columns — "source" (model/image) is implementation detail, not
        # something the farmer needs to see.
        c1, c2, c3 = st.columns(3)
        c1.metric(T["grain"], _tr(result.get("millet", "?").title(), lang_choice))
        c2.metric(T["grade"], result.get("grade", "?"))
        c3.metric(T["confidence"], f"{result.get('quality_score',0)*100:.1f}%")
    if result.get("top3"):
        with st.expander(T["top3"]):
            for t in result["top3"]:
                st.progress(t["prob"], text=f"{_tr(t['class'], lang_choice)} — {t['prob']*100:.1f}%")

    st.divider()

    # --- Agent 2: Price ----------------------------------------------------
    st.header(T["price_header"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T["expected_price"], f"₹{result.get('expected_price',0):,.0f}")
    c2.metric(T["trend"], disp_trend)
    # Total revenue — emphasized in 36px green (most important number for the farmer)
    with c3:
        st.markdown(
            f"<div class='ms-revenue-label'>{T['total_revenue']}</div>"
            f"<div class='ms-revenue-value'>₹{result.get('expected_total_revenue',0):,.0f}</div>"
            f"<div class='ms-en-sub'>Total revenue</div>",
            unsafe_allow_html=True,
        )
    c4.metric(T["model_confidence"], f"{result.get('confidence',0)*100:.0f}%")
    pr = result.get("price_range")
    if pr:
        st.caption(f"{T['price_range']}: ₹{pr[0]:,.0f} – ₹{pr[1]:,.0f}")

    # 12-month price sparkline — wrapped in a bordered container that the
    # global CSS styles into a cream + olive call-out box matching the
    # recommendation box at the top of the page.
    try:
        hist_df = get_price_history()
        millet_low = (result.get("millet") or "").lower()
        farmer_state = result.get("farmer_state") or "Maharashtra"
        farmer_district = result.get("farmer_district") or "Pune"
        slc = hist_df[
            (hist_df["millet"] == millet_low)
            & (hist_df["state"] == farmer_state)
            & (hist_df["district"] == farmer_district)
        ].sort_values(["year", "month"]).tail(12)
        if not slc.empty and len(slc) >= 3:
            slc = slc.copy()
            slc["period"] = slc["year"].astype(str) + "-" + slc["month"].astype(str).str.zfill(2)
            chart_df = slc.set_index("period")[["modal_price"]]
            chart_df.columns = [T["expected_price"]]
            with st.container(border=True):
                st.markdown(
                    f"**📈 {_tr('Last 12 months', lang_choice)} — "
                    f"{_tr(farmer_district, lang_choice)} ({millet_low})**"
                )
                st.line_chart(chart_df, height=160, use_container_width=True)
    except Exception:
        pass

    st.divider()

    # --- Agent 3: Market ---------------------------------------------------
    st.header(T["market_header"])
    best = result.get("best_market") or {}
    local = result.get("local_market") or {}
    msp_check = result.get("msp_check") or {}

    if best:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["best_market"], _tr(best.get("market", "-"), lang_choice))
        c2.metric(T["net_per_q"], f"₹{best.get('net_price_per_q',0):,.0f}")
        c3.metric(T["distance"], f"{best.get('distance_km',0)} km")
        c4.metric(T["total_net_rev"], f"₹{best.get('total_net_revenue',0):,.0f}")

    if local and local.get("market") != best.get("market"):
        st.caption(
            f"{T['nearest']}: **{_tr(local.get('market',''), lang_choice)}** "
            f"({local.get('distance_km',0)} km) — ₹{local.get('net_price_per_q',0):,.0f}/q"
        )

    top5 = result.get("top_5_nearest") or []
    if top5:
        import pandas as pd
        df = pd.DataFrame(top5)[[
            "market", "district", "distance_km", "apmc_price",
            "transport_per_q", "commission_per_q", "net_price_per_q", "total_net_revenue",
        ]]
        # Identify the winning row by net price BEFORE we format strings
        winner_idx = int(df["net_price_per_q"].idxmax())

        # Translate market & district names if not in English mode
        if lang_choice != "English":
            df["market"]   = df["market"].apply(lambda x: _tr(x, lang_choice))
            df["district"] = df["district"].apply(lambda x: _tr(x, lang_choice))
        df = df.rename(columns={
            "market": T["tbl_market"], "district": T["tbl_district"],
            "distance_km": T["tbl_dist"], "apmc_price": T["tbl_apmc"],
            "transport_per_q": T["tbl_transport"], "commission_per_q": T["tbl_comm"],
            "net_price_per_q": T["tbl_net"], "total_net_revenue": T["tbl_total"],
        })
        df[T["tbl_dist"]] = df[T["tbl_dist"]].apply(lambda x: f"{x:.1f}")
        for col in [T["tbl_apmc"], T["tbl_transport"], T["tbl_comm"], T["tbl_net"], T["tbl_total"]]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"₹{x:,.0f}")

        # Highlight winning row: pale green background + bold + green left border
        def _highlight_winner(row):
            if row.name == winner_idx:
                return [
                    "background-color: #ecfdf5; "
                    "font-weight: 600; "
                    "border-left: 4px solid #10b981;"
                ] * len(row)
            return [""] * len(row)

        styled = df.style.apply(_highlight_winner, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)

    shared = result.get("shared_transport_opportunity")
    if shared:
        st.info(f"{T['shared_transport']} {_tr(shared.get('message',''), lang_choice)}")

    m_insights = result.get("market_insights") or []
    if m_insights:
        with st.expander(T["market_insights"], expanded=True):
            for i in m_insights:
                st.markdown(f"- {_tr(i, lang_choice)}")

    st.divider()

    # --- Agent 4: Decision details -----------------------------------------
    st.header(T["decision_header"])
    shelf = result.get("shelf_life") or {}
    weather = result.get("weather") or {}
    fest = result.get("next_festival")

    # Traffic-light cards: weather risk · shelf life · festival countdown
    risk_level, risk_label_mr, risk_color = _weather_risk(weather)
    shelf_days = int(shelf.get("days") or 0)
    shelf_pct = max(0.0, min(1.0, shelf_days / 30.0))
    shelf_color = "green" if shelf_days >= 20 else ("amber" if shelf_days >= 10 else "red")
    weather_summary_short = _tr(weather.get("summary", "-"), lang_choice)
    shelf_note_short = _tr(shelf.get("note", "—"), lang_choice)

    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        st.markdown(
            f"<div class='ms-card ms-card-{risk_color}'>"
            f"<div class='ms-card-title'>{T['weather_outlook']}<div class='ms-en-sub'>Weather risk</div></div>"
            f"<div class='ms-card-value'>{risk_label_mr}</div>"
            f"<div class='ms-card-sub'>{weather_summary_short}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with tc2:
        st.markdown(
            f"<div class='ms-card ms-card-{shelf_color}'>"
            f"<div class='ms-card-title'>{T['shelf_life']}<div class='ms-en-sub'>Shelf life</div></div>"
            f"<div class='ms-card-value'>{shelf_days} / 30 {T['days']}</div>"
            f"<div class='ms-card-sub'>{shelf_note_short}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with tc3:
        if fest:
            fest_name_disp = _tr(fest["name"], lang_choice)
            fest_reason_disp = _tr(fest["reason"], lang_choice)
            # Festival demand is always amber — represents an opportunity, not a
            # safe/risk binary. Same colour regardless of spike size.
            st.markdown(
                f"<div class='ms-card ms-card-amber'>"
                f"<div class='ms-card-title'>{T['festival_driver']}<div class='ms-en-sub'>Festival demand</div></div>"
                f"<div class='ms-card-value'>{fest_name_disp} · {fest['days_away']} {T['days']}</div>"
                f"<div class='ms-card-sub'>+{fest['spike_pct']}% — {fest_reason_disp}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='ms-card'>"
                f"<div class='ms-card-title'>{T['festival_driver']}<div class='ms-en-sub'>Festival demand</div></div>"
                f"<div class='ms-card-value'>—</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ----- संपूर्ण तर्क · Full reasoning ------------------------------------
    # These bullets come from Agent 4's `decision_insights` and explain WHY
    # the rule engine picked the recommendation it did — the first bullet is
    # the actual decision reason ("Prices trending up... hold for better
    # price"), the rest add supporting context (shelf, weather, festival).
    st.markdown("")  # small spacer
    st.subheader(T["full_reasoning"])
    decision_insights = result.get("decision_insights") or []
    for line in decision_insights:
        st.markdown(
            f"<div class='ms-reason'>•  {_tr(line, lang_choice)}</div>",
            unsafe_allow_html=True,
        )

    msp_adv = result.get("msp_advisory")
    if msp_adv:
        msp_msg = (
            f"MSP = ₹{msp_adv['msp_per_quintal']}/q, "
            f"₹{msp_adv['gap_per_quintal']} more than APMC net ₹{msp_adv['your_best_net']}/q. "
            f"₹{msp_adv['extra_total_if_govt']} extra for {result.get('quantity_quintal', '?')}q. "
            f"Check eNAM / FCI."
        )
        st.info(f"{T['msp_alt']} {_tr(msp_msg, lang_choice)}")

    st.divider()


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
                     "next_festival", "msp_advisory", "decision_insights", "explanation"],
        "quality_retry": ["retry_image_path", "reflection_retries", "reflection_note"],
        "human_review": ["action", "reason", "status", "risk", "issues", "decision_insights"],
    }

    AGENT_ROLE = {
        "quality":       ("🔍 Agent 1", "Quality Assessment", "EfficientNetB0 CNN"),
        "geocode":       ("📍 Tool",    "Geocoding",         "Nominatim OSM"),
        "market":        ("🗺️ Agent 3", "Market Comparison",  "XGBoost + OSRM"),
        "weather":       ("🌦️ Tool",    "Weather Forecast",  "Open-Meteo API"),
        "price":         ("💰 Agent 2", "Price Prediction",  "XGBoost regressor"),
        "decision":      ("🧠 Agent 4", "Decision Advisor",  "Rules + bilingual summary"),
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
