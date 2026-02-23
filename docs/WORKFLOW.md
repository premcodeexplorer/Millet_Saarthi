# MilletSaarthi — Build Workflow & Project Structure

## Project Structure (Final)

```
MilletSaarthi/
│
├── CLAUDE.md                        # Project memory for Claude Code
├── README.md                        # Project documentation
├── requirements.txt                 # All Python dependencies
├── .env                             # API keys (NEVER commit)
├── .env.example                     # Template for .env
├── .gitignore                       # Ignore models, .env, __pycache__, venv
├── setup.py                         # Optional package setup
│
├── app/                             # --- APPLICATION LAYER ---
│   ├── __init__.py
│   ├── main.py                      # Streamlit entry point (UI)
│   ├── orchestrator.py              # Central pipeline controller
│   ├── config.py                    # App-wide constants, paths, thresholds
│   └── utils.py                     # Shared helpers (logging setup, JSON validators)
│
├── agents/                          # --- AGENT LAYER (core logic) ---
│   ├── __init__.py
│   ├── base_agent.py                # Abstract base class all agents inherit
│   ├── quality_agent.py             # Agent 1: Grain type + grade classification
│   ├── price_agent.py               # Agent 2: Price prediction (LSTM + XGBoost)
│   ├── market_agent.py              # Agent 3: APMC market comparison
│   └── decision_agent.py            # Agent 4: Sell/hold recommendation
│
├── models/                          # --- TRAINED MODEL ARTIFACTS ---
│   ├── quality_model/
│   │   ├── resnet50_grain.h5        # Keras saved model
│   │   └── class_labels.json        # Label index mapping
│   └── price_model/
│       ├── lstm_price.h5            # LSTM model
│       ├── xgboost_price.pkl        # XGBoost model
│       └── scaler.pkl               # Feature scaler
│
├── data/                            # --- DATA LAYER ---
│   ├── grain_images/                # Raw + augmented training images
│   │   ├── bajra/
│   │   ├── jowar/
│   │   └── ragi/
│   ├── agmarknet/                   # Historical price CSVs
│   │   ├── raw/                     # Original scraped data
│   │   └── cleaned/                 # Processed, ready-to-train data
│   ├── apmc_markets.json            # 20+ markets with lat/long/commission
│   ├── festival_calendar.csv        # Festival dates + demand spike levels
│   └── shelf_life_rules.json        # Moisture-based storage thresholds
│
├── preprocessing/                   # --- DATA PREPARATION ---
│   ├── __init__.py
│   ├── image_preprocessor.py        # OpenCV: resize, denoise, contrast
│   ├── augmentation.py              # ImageDataGenerator augmentation
│   └── price_data_cleaner.py        # Clean Agmarknet CSVs
│
├── training/                        # --- MODEL TRAINING ---
│   ├── __init__.py
│   ├── train_quality_model.py       # ResNet50 fine-tuning script
│   └── train_price_model.py         # LSTM + XGBoost training script
│
├── templates/                       # --- FRONTEND (if Flask later) ---
│   └── index.html
│
├── static/                          # --- STATIC ASSETS ---
│   ├── css/
│   ├── js/
│   └── images/
│
├── tests/                           # --- TESTING ---
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures (sample images, mock data)
│   ├── test_quality_agent.py
│   ├── test_price_agent.py
│   ├── test_market_agent.py
│   ├── test_decision_agent.py
│   └── test_orchestrator.py         # End-to-end pipeline test
│
├── notebooks/                       # --- EXPLORATION ---
│   ├── eda_grain_images.ipynb       # Image dataset analysis
│   └── eda_price_data.ipynb         # Price trend analysis
│
└── docs/                            # --- DOCUMENTATION ---
    ├── WORKFLOW.md                   # THIS FILE
    ├── synopsis.pdf
    ├── architecture_diagram.png
    └── research_paper/
```

---

## Build Workflow (Step-by-Step)

### STAGE 1: Foundation (Days 1-3)

**Goal:** Project skeleton, dependencies, data files ready.

```
Step 1.1  Create all directories from structure above
Step 1.2  Create .gitignore (models/, .env, __pycache__, venv/, *.h5, *.pkl, data/grain_images/)
Step 1.3  Create .env.example with placeholder keys
Step 1.4  Create requirements.txt with all dependencies
Step 1.5  Create app/config.py with all constants (paths, thresholds, API URLs)
Step 1.6  Create app/utils.py with logging setup + JSON schema validators
Step 1.7  Create agents/base_agent.py — abstract base class with process() and validate_input()
Step 1.8  Create data/apmc_markets.json (20+ Maharashtra APMC markets)
Step 1.9  Create data/festival_calendar.csv (2025-2026 festivals)
Step 1.10 Create data/shelf_life_rules.json (moisture thresholds)
Step 1.11 Git commit: "feat: initialize project structure and static data"
```

**Deliverables:** Runnable skeleton, all static data files, base agent class.

---

### STAGE 2: Agent 1 — Quality Assessment (Days 4-10)

**Goal:** Given a grain image, classify type (Bajra/Jowar/Ragi) and grade (A/B/C).

```
Step 2.1  Download Grain Class Image Dataset → organize into data/grain_images/{bajra,jowar,ragi}/
Step 2.2  Build preprocessing/image_preprocessor.py
          - Resize to 224x224
          - Gaussian blur removal (denoise)
          - CLAHE contrast enhancement
          - Laplacian variance blur detection (reject < threshold)
Step 2.3  Build preprocessing/augmentation.py
          - Rotation (±30°), horizontal/vertical flip
          - Brightness (±20%), zoom (0.8-1.2x)
          - Target: 5K raw → 15K+ augmented
Step 2.4  Build training/train_quality_model.py
          - Load ResNet50 (imagenet weights, exclude top)
          - Add: GlobalAveragePooling → Dense(256, relu) → Dropout(0.3) → Dense(num_classes, softmax)
          - Freeze base layers, train top → unfreeze last 20 layers, fine-tune
          - 70/15/15 train/val/test split
          - Save to models/quality_model/resnet50_grain.h5
Step 2.5  Build agents/quality_agent.py
          - Loads saved model
          - process() takes {"image_path": "..."} → returns {"millet", "grade", "quality_score", "confidence"}
          - validate_input() checks image exists, is valid format, not blurry
Step 2.6  Build tests/test_quality_agent.py
          - Test with known good images
          - Test with blurry image (should reject)
          - Test with non-image file (should error gracefully)
Step 2.7  Git commit: "feat(agent1): quality assessment with ResNet50"
```

**Deliverables:** Trained model, working agent, passing tests.

---

### STAGE 3: Agent 2 — Price Prediction (Days 11-20)

**Goal:** Predict expected price per quintal based on grain type, grade, and historical trends.

```
Step 3.1  Scrape/download Agmarknet data → data/agmarknet/raw/
          - Bajra, Jowar, Ragi prices from 2015-2025
          - Fields: date, market, commodity, variety, min_price, max_price, modal_price
Step 3.2  Build preprocessing/price_data_cleaner.py
          - Handle missing values (forward-fill for time series)
          - Remove outliers (IQR method)
          - Normalize prices
          - Feature engineering: month, season, day_of_week, lag_7d, lag_30d, rolling_mean
          - Save to data/agmarknet/cleaned/
Step 3.3  Build training/train_price_model.py
          - LSTM branch: sequence of last 30 days prices → predict next price
          - XGBoost branch: tabular features (season, grade, market, lags) → predict price
          - Ensemble: weighted average (0.6 LSTM + 0.4 XGBoost, tunable)
          - Time-based split: train < 2023, val = 2023, test = 2024-2025
          - Save models to models/price_model/
Step 3.4  Build agents/price_agent.py
          - process() takes Agent 1 output → returns {"expected_price", "confidence", "trend", "price_range"}
          - Uses grade to adjust prediction (Grade A: +5-10%, Grade C: -5-10%)
          - validate_input() checks required fields from Agent 1
Step 3.5  Build tests/test_price_agent.py
          - Test with known commodity+grade → price within expected range
          - Test grade adjustment logic
          - Test with missing fields → graceful error
Step 3.6  Git commit: "feat(agent2): price prediction with LSTM + XGBoost ensemble"
```

**Deliverables:** Trained ensemble model, quality-aware pricing, passing tests.

---

### STAGE 4: Agent 3 — Market Comparison (Days 21-28)

**Goal:** Find the best APMC market after accounting for transport costs and commission.

```
Step 4.1  Build agents/market_agent.py
          - Load apmc_markets.json (market name, lat, long, commission_rate)
          - Scrape current prices from Agmarknet (BeautifulSoup + requests)
          - Calculate distance: Google Maps Distance Matrix API (farmer location → each market)
          - Transport cost = distance_km × rate_per_km × quantity_quintals
          - Net profit = market_price × quantity - transport_cost - (commission_rate × market_price × quantity)
          - Rank markets by net profit, return top 3-5
          - process() takes Agent 2 output + farmer_location + quantity
          - Returns {"markets": [...], "best_market", "best_net_profit", "distance_km"}
Step 4.2  Add fallback: if scraping fails, use Agent 2 predicted price as baseline
Step 4.3  Add caching: cache API responses for 1 hour (avoid rate limits)
Step 4.4  Build tests/test_market_agent.py
          - Test with mock APMC data (no live scraping in tests)
          - Test transport cost calculation
          - Test ranking logic
          - Test scraping failure fallback
Step 4.5  Git commit: "feat(agent3): market comparison with transport cost calculation"
```

**Deliverables:** Working market ranker, API integration, fallback handling.

---

### STAGE 5: Agent 4 — Decision Advisor (Days 29-35)

**Goal:** Combine all agent outputs into a final SELL_NOW / HOLD / SELL_LATER recommendation.

```
Step 5.1  Build agents/decision_agent.py
          - Weather check: OpenWeatherMap 5-day forecast → rain/storm = urgency to sell
          - Shelf life check: moisture level → days until spoilage
          - Festival check: upcoming festivals → demand spike expected?
          - Price trend check: from Agent 2, is price rising or falling?
          - Cross-verification: flag contradictions (Grade A + low price = suspicious)
          - Decision logic (priority order):
            1. Moisture > 14% → SELL_NOW (urgent, grain will spoil)
            2. Rain forecast in 3 days + outdoor storage → SELL_NOW
            3. Festival in 7 days + price rising → HOLD (sell during festival)
            4. Price falling + no festival → SELL_NOW
            5. Default: SELL_NOW at best market
          - process() returns {"action", "market", "reason", "risk_level", "confidence", "warnings"}
Step 5.2  Implement contradiction detection
          - Grade A but price < MSP → warning
          - Agent 2 says rising but Agent 3 live prices falling → warning
          - Distance > 200km → high transport risk warning
Step 5.3  Build tests/test_decision_agent.py
          - Test each decision path (moisture urgent, rain, festival, default)
          - Test contradiction detection
          - Test with missing weather data (should still work with reduced confidence)
Step 5.4  Git commit: "feat(agent4): decision advisor with cross-verification"
```

**Deliverables:** Complete decision engine, contradiction detection, all decision paths tested.

---

### STAGE 6: Orchestrator + Integration (Days 36-42)

**Goal:** Wire all 4 agents into one pipeline, controlled by the orchestrator.

```
Step 6.1  Build app/orchestrator.py
          - Pipeline: image input → Agent 1 → Agent 2 → Agent 3 → Agent 4 → final output
          - Error handling: if any agent fails, return partial results + error info
          - Logging: log each agent's input/output for debugging
          - Timeout: 30s per agent, 120s total pipeline
          - Returns combined JSON with all agent outputs + final recommendation
Step 6.2  Build tests/test_orchestrator.py
          - End-to-end test with sample image
          - Test partial failure (Agent 3 scraping fails → still get quality + price + decision)
          - Test timeout handling
Step 6.3  Git commit: "feat(orchestrator): central pipeline controller"
```

**Deliverables:** Working end-to-end pipeline, error resilience.

---

### STAGE 7: Frontend — Streamlit UI (Days 43-50)

**Goal:** Farmer-facing interface in Streamlit.

```
Step 7.1  Build app/main.py (Streamlit)
          - Page 1: Upload image + enter location (text or map pin) + quantity
          - Page 2: Results dashboard
            - Quality card: grain type, grade, confidence score, image preview
            - Price card: expected price, trend chart, confidence
            - Market card: top 3 markets table (name, distance, net profit), mini map
            - Decision card: action (SELL_NOW/HOLD), reason, risk level, warnings
          - Sidebar: language toggle (English / Marathi)
Step 7.2  Add Marathi translations for all UI strings
Step 7.3  Add loading spinners per agent (show pipeline progress)
Step 7.4  Add error states (blurry image warning, API timeout message)
Step 7.5  Git commit: "feat(ui): Streamlit frontend with bilingual support"
```

**Deliverables:** Complete UI, bilingual, responsive to all pipeline states.

---

### STAGE 8: Testing & Polish (Days 51-56)

**Goal:** Full test coverage, documentation, demo-ready.

```
Step 8.1  Run all unit tests, fix failures
Step 8.2  Run end-to-end tests with 10+ different images
Step 8.3  Performance benchmarking (time per agent, total pipeline time)
Step 8.4  Write README.md (setup, usage, architecture, screenshots)
Step 8.5  Create architecture_diagram.png
Step 8.6  Final git tag: "v1.0.0"
```

---

## Dependency Graph

```
Stage 1 (Foundation)
   │
   ├── Stage 2 (Agent 1: Quality) ──────────┐
   │                                         │
   │   Stage 3 (Agent 2: Price) ◄────────────┘
   │       │
   │       ├── Stage 4 (Agent 3: Market) ◄───┘
   │       │
   │       └── Stage 5 (Agent 4: Decision) ◄── Stages 2+3+4
   │
   └── Stage 6 (Orchestrator) ◄── Stages 2+3+4+5
           │
           └── Stage 7 (Frontend) ◄── Stage 6
                   │
                   └── Stage 8 (Testing & Polish)
```

---

## Key Technical Decisions

| Decision              | Choice                            | Rationale                                       |
| --------------------- | --------------------------------- | ----------------------------------------------- |
| Base class for agents | Abstract `BaseAgent`              | Enforces consistent interface, easier testing   |
| Agent communication   | JSON dicts via orchestrator       | Simple, debuggable, no message queue overhead   |
| Model format          | .h5 (Keras) + .pkl (sklearn)      | Standard, easy to load/save                     |
| Frontend              | Streamlit                         | Rapid prototyping, built-in widgets for ML apps |
| Price ensemble        | 0.6 LSTM + 0.4 XGBoost            | LSTM handles trends, XGBoost handles features   |
| Testing               | pytest + mock                     | Mock external APIs, test logic in isolation     |
| Scraping fallback     | Use predicted price if live fails | System never fully breaks                       |

---

## requirements.txt (Reference)

```
# Core
python-dotenv==1.0.1
streamlit>=1.30.0

# ML / Deep Learning
tensorflow>=2.15.0
xgboost>=2.0.0
scikit-learn>=1.4.0

# Image Processing
opencv-python>=4.9.0
Pillow>=10.2.0

# Data
pandas>=2.2.0
numpy>=1.26.0
matplotlib>=3.8.0
seaborn>=0.13.0

# Web Scraping
beautifulsoup4>=4.12.0
requests>=2.31.0

# Database
psycopg2-binary>=2.9.9
SQLAlchemy>=2.0.0

# API
googlemaps>=4.10.0

# Testing
pytest>=8.0.0
pytest-cov>=4.1.0

# Logging
loguru>=0.7.0
```
