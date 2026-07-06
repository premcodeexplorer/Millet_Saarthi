# 🌾 MilletSaarthi

> **An AI-powered selling advisor for small Indian millet farmers.**
> Take a phone photo of your grain, type your village and quantity — and get one clear answer: **Sell now, sell urgently, or wait — and where will you get the most money?**

MilletSaarthi ("Millet Companion / Charioteer") is a **multi-agent decision system** that fuses computer vision, time-series ML, geospatial routing, and real-world signals (weather, festivals, MSP, shelf life) into a single bilingual recommendation — delivered in **Marathi, Hindi, or English** in under 10 seconds.

---

## The Problem

- **86%** of Indian farmers are small or marginal. Millets — jowar, bajra, ragi — are their cash crop.
- At the APMC mandi they sell **blindly**: they don't know the real grade of their grain, next month's price trend, whether a farther mandi pays more *net* after transport, or whether weather will spoil their grain if they wait.
- Result: **20–30% income loss per harvest.**

**Our solution:** one phone-friendly app that answers all of this, in the farmer's own language.

---

## How It Works

MilletSaarthi is **not** a fixed `Agent1 → Agent2 → Agent3 → Agent4` pipeline. An **Orchestrator** holds a shared state dict and asks a **Planner** at every step what to run next. The Planner can run agents **in parallel**, **skip** agents whose answer is already known, **retry** on low confidence (reflection loop), or **short-circuit to human review** on a blurry image.

```
FARMER INPUT (photo + village + quantity)
        │
        ▼
   ORCHESTRATOR ──► PLANNER  (state-driven routing brain)
        │
   Iter 1:  Agent 1 (Quality CNN)   ‖  Geocode tool        (parallel)
   Iter 2:  Agent 3 (Market rank)   ‖  Weather tool        (parallel)
   Iter 3:  Agent 2 (Price trend)                          (skipped if urgent)
   Iter 4:  Agent 4 (Decision advisor → SELL_NOW / WAIT / URGENT_SELL)
        │
        ▼
   STREAMLIT UI  (Tab 1: Farmer dashboard · Tab 2: Planner trace)
```

### The Four Agents

| | **Agent 1 — Quality** | **Agent 2 — Price** | **Agent 3 — Market** | **Agent 4 — Decision** |
|---|---|---|---|---|
| **Role** | Identify millet & grade from photo | Predict ₹/quintal at any APMC | Rank APMCs by net profit | Final SELL / WAIT recommendation |
| **Model** | EfficientNetB0 (transfer learning) | XGBoost regressor | XGBoost + OSRM routing + Haversine | Deterministic rule tree |
| **External calls** | None (local) | None | Nominatim + OSRM | Open-Meteo |
| **Fallback** | Blur + confidence gates | Mock on unseen category | Haversine × 1.3 if OSRM down | Neutral weather if API fails |

- **Agent 1** grades 7 classes (Bajra A/B, Jowar A/B/C, Ragi A/B) with blur and 0.75-confidence safety gates.
- **Agent 2** uses 11 features including cyclical month encoding and lag features from real price history; grade multipliers (A ×1.10, B ×1.00, C ×0.88) applied post-prediction.
- **Agent 3** ranks 30 APMCs (16 Maharashtra + 14 Karnataka) by **net ₹/quintal** after transport and commission, checks MSP, and suggests **shared-transport** group selling.
- **Agent 4** fuses everything with weather, festival calendar, and shelf life into one of `SELL_NOW / URGENT_SELL / WAIT / HOLD_CAUTION / HUMAN_REVIEW`, plus a bilingual explanation (pure template — no LLM, no network).

---

## Coverage

| Aspect | Coverage |
|---|---|
| **Millets** | Jowar (ज्वारी), Bajra (बाजरी), Ragi (नाचणी) |
| **Grades** | A, B, C (C only for Jowar) — 7 classes |
| **States / Mandis** | Maharashtra (16) + Karnataka (14) = **30 APMCs** |
| **Languages** | Marathi (default), Hindi, English |
| **Price history** | 1,854 monthly rows, 2021–2026 |

---

## Quick Start

```bash
# 1. Install dependencies (Python 3.10+)
pip install -r requirements.txt

# 2. Launch the app
python run.py
```

Then open **http://localhost:8501**, upload a grain photo, enter a village (e.g. *Baramati, Maharashtra*) and quantity (e.g. *10 quintals*), and click **Get Recommendation**.

> `run.py` loads `torch` before Streamlit on Windows to avoid a DLL conflict.

> **Internet** is needed for the free geocoding/routing/weather APIs (Nominatim, OSRM, Open-Meteo) — but each has a fallback, so the app degrades gracefully rather than crashing.

### Optional configuration

Create a `.env` file for optional paid-API fallbacks (not required for the demo):

```
LOCATIONIQ_KEY=...     # paid geocoding fallback (e.g. on Streamlit Cloud where Nominatim is blocked)
OPENWEATHER_KEY=...     # optional weather key
```

---

## Project Structure

```
MilletSaarthi/
├── app/
│   ├── main.py            # Streamlit UI (trilingual, two tabs)
│   ├── orchestrator.py    # Multi-agent executor (shared state + thread pool)
│   ├── planner.py         # State-driven router (the agentic brain)
│   └── config.py          # Paths, thresholds, API URLs
├── agents/
│   ├── quality_agent.py   # Agent 1 — EfficientNetB0
│   ├── price_agent.py     # Agent 2 — XGBoost regressor
│   ├── market_agent.py    # Agent 3 — XGBoost + OSRM + Nominatim
│   └── decision_agent.py  # Agent 4 — rule engine + Open-Meteo
├── notebooks/             # Training notebooks (one per agent)
├── data/
│   ├── master_prices.csv  # 1,854 rows, 2021–2026
│   └── apmc_markets.json  # 30 APMCs: MSP, truck rental, commission
├── models/
│   ├── price_model.json   # XGBoost (portable JSON, not pickle)
│   ├── encoders.pkl       # LabelEncoders
│   ├── features.txt       # Feature column order
│   └── classes.json       # 7 quality classes
├── best_model.h5          # EfficientNetB0 checkpoint (~28 MB)
├── price_data/            # Raw mandi CSVs
├── run.py                 # Launcher
└── requirements.txt
```

---

## Tech Stack

**Python 3.10+** · **Streamlit** (UI) · **TensorFlow/Keras** (Agent 1 CNN) · **XGBoost** (Agents 2 & 3) · **Pillow** (image preprocessing) · **pandas** (price-history lookup) · **requests** (Nominatim / OSRM / Open-Meteo) · **deep-translator** (UI translation) · `ThreadPoolExecutor` (parallel dispatch).

No paid APIs are required for the demo — Nominatim, OSRM, and Open-Meteo are all free.

---

## What Makes It Unique

1. **Genuinely agentic** — the Planner re-evaluates after every step: parallel dispatch, conditional skipping, reflection retry, short-circuit to human review.
2. **Real ML on real data** — EfficientNetB0 on a hand-collected APMC dataset; XGBoost on 1,854 rows of real price history with lag features.
3. **Bulk-aware economics** — transport spreads across truck capacity; shared-transport suggestions unlock collective bargaining.
4. **Multilingual, farmer-first UX** — Marathi default, traffic-light cards, big revenue number, no jargon.
5. **Failure-resilient** — every external call has a fallback; the pipeline never crashes.
6. **Transparent** — Tab 2 shows every planner decision and full agent output for auditability.

---

## Team

**VI sem AIML — RCOEM Nagpur**

- **Prem Baba** — Lead · Orchestrator + Planner + Agent 4 (Decision)
- **Purva** — Agent 1 (Quality)
- **Palak** — Agent 2 (Price)
- **Adhishree** — Agent 3 (Market)

> For a full technical deep-dive and presentation notes, see [`PRESENTATION.md`](PRESENTATION.md).
