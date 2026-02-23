# CLAUDE.md — MilletSaarthi Project Memory

> **This file is the project memory for Claude Code. Place it in the root of your project directory.**
> Claude Code reads this file automatically every session to understand context, rules, and what to do.

---

## 🧠 Project Identity

**Project Name:** MilletSaarthi — A Multi-Agent Intelligence System for Smart Millet Market Decisions  
**Team:** Group 7, Section B, VI Semester (AIML), RCOEM Nagpur  
**Guide:** Dr. Nisarg Gandhewar  
**Members:** Prem Baba (Lead, Roll 53), Purva Bhoyar (57), Adhishree Shiledar (01), Palak Zade (68)  
**Session:** 2025-26 EVEN Semester  
**Tech Stack:** Python, Flask/Streamlit, TensorFlow/PyTorch, PostgreSQL, OpenCV

---

## 🎯 What Is MilletSaarthi?

A web-based multi-agent AI system that helps millet farmers (Bajra, Jowar, Ragi) make smart selling decisions. The farmer uploads ONE grain image, and the system tells them:
- **What** grain and quality grade (A/B/C) they have
- **What price** to expect based on quality + historical trends
- **Where** to sell (best APMC market after transport costs)
- **When** to sell (weather, shelf life, festival demand)

**Core Innovation:** No existing system integrates quality assessment → price prediction → market comparison → decision support as one pipeline. All prior work treats these as separate problems.

---

## 🏗️ System Architecture (4 Agents + Orchestrator)

```
Farmer Input (image + location + quantity)
        │
        ▼
┌─────────────────────────┐
│   CENTRAL ORCHESTRATOR  │ ← Manages data flow between agents (JSON)
└─────────┬───────────────┘
          │
    ┌─────┼─────────────────────────────┐
    ▼     ▼              ▼              ▼
┌───────┐ ┌───────┐ ┌──────────┐ ┌──────────┐
│Agent 1│→│Agent 2│→│ Agent 3  │→│ Agent 4  │
│Quality│ │Price  │ │ Market   │ │ Decision │
└───────┘ └───────┘ └──────────┘ └──────────┘
    │         │           │            │
    ▼         ▼           ▼            ▼
 CNN/       LSTM+      Web Scrape   Decision
 ResNet50   XGBoost    + Maps API   Tree + Rules
```

### Agent 1 — Quality Assessment
- **Input:** Grain image from farmer
- **Process:** OpenCV preprocessing → CNN (ResNet50 transfer learning from ImageNet)
- **Output JSON:** `{ "millet": "Bajra", "grade": "A", "quality_score": 0.87 }`
- **Grading Criteria:**
  - Grade A: <2% broken grains, <1% foreign matter
  - Grade B: 2-5% broken, 1-3% foreign matter
  - Grade C: >5% broken, >3% foreign matter
- **Dataset:** Grain Class Image Dataset (Universe by Vinit), ~5K images → 15K+ after augmentation
- **Image specs:** 224×224px RGB, augmentation (rotation, flip, brightness, zoom)
- **Expected accuracy:** 88-93% type classification, 80-85% grading

### Agent 2 — Price Prediction
- **Input:** Agent 1 output + Agmarknet historical data + seasonal trends
- **Process:** LSTM (temporal patterns) + XGBoost (feature-based) → ensemble
- **Output JSON:** `{ "expected_price": 3150, "confidence": 0.81, "trend": "rising" }`
- **Key feature:** Quality-aware pricing — Grade A gets different prediction than Grade C
- **Dataset:** Agmarknet (agmarknet.gov.in), ~50K+ records, daily prices 2010-2025
- **Features:** millet_type, grade, date, season, market, previous_prices, rainfall, temperature
- **Expected accuracy:** MAPE 5-15% (under ₹100-150/quintal error)

### Agent 3 — Market Comparison
- **Input:** Agent 2 output + farmer location + quantity
- **Process:** BeautifulSoup scraping APMC prices + Google Maps Distance Matrix API
- **Output JSON:** `{ "best_market": "Aurangabad APMC", "net_profit": 3020, "distance_km": 38 }`
- **Transport cost:** ₹15-25/km/quintal (standard rate)
- **Effective profit** = market_price − transport_cost − commission
- **No ML model** — purely API-driven calculation
- **Coverage:** 20+ APMC markets with lat/long and commission rates

### Agent 4 — Decision Advisor
- **Input:** All 3 agent outputs + IMD weather API + shelf life rules + festival calendar
- **Process:** Decision tree logic + cross-agent verification
- **Output JSON:** `{ "action": "SELL_NOW", "market": "Aurangabad", "reason": "Rain in 3 days", "status": "VERIFIED", "risk": "LOW" }`
- **Shelf life rules:**
  - <12% moisture → 30+ days safe
  - 12-14% moisture → 15-20 days
  - >14% moisture → 7-10 days (urgent sell)
- **Verification:** Flags contradictions (e.g., Grade A but very low predicted price)
- **Why decision tree:** Explainability (farmer needs to know WHY), no training data exists for this task

### Agent Communication
- All agents communicate through **structured JSON** via a Central Orchestrator
- Agent 1 → Agent 2 → Agent 3 → Agent 4 (sequential pipeline)
- Agent 4 can flag contradictions across agents (cross-verification)

---

## 📁 Expected Project Structure

```
MilletSaarthi/
├── CLAUDE.md                    ← THIS FILE (project memory)
├── README.md                    ← Project documentation
├── requirements.txt             ← Python dependencies
├── .env                         ← API keys (Google Maps, OpenWeatherMap) — NEVER COMMIT
├── .gitignore
│
├── app/                         ← Main application
│   ├── __init__.py
│   ├── main.py                  ← Flask/Streamlit entry point
│   ├── orchestrator.py          ← Central agent orchestrator
│   └── config.py                ← Configuration and constants
│
├── agents/                      ← All 4 agents
│   ├── __init__.py
│   ├── quality_agent.py         ← Agent 1: CNN/ResNet50 grain classification
│   ├── price_agent.py           ← Agent 2: LSTM + XGBoost price prediction
│   ├── market_agent.py          ← Agent 3: APMC scraping + transport cost
│   └── decision_agent.py        ← Agent 4: Decision tree + verification
│
├── models/                      ← Trained model files (.h5, .pkl, .pt)
│   ├── quality_model/
│   └── price_model/
│
├── data/                        ← Datasets and static data
│   ├── grain_images/            ← Training images (Bajra/Jowar/Ragi)
│   ├── agmarknet/               ← Historical price CSVs
│   ├── apmc_markets.json        ← Market database (lat/long, commission)
│   ├── festival_calendar.csv    ← Festival demand spike dates
│   └── shelf_life_rules.json    ← Moisture-based shelf life thresholds
│
├── preprocessing/               ← Data preparation scripts
│   ├── image_preprocessor.py    ← OpenCV preprocessing pipeline
│   ├── price_data_cleaner.py    ← Agmarknet data cleaning
│   └── augmentation.py          ← Image augmentation pipeline
│
├── training/                    ← Model training scripts
│   ├── train_quality_model.py   ← ResNet50 fine-tuning
│   └── train_price_model.py     ← LSTM + XGBoost training
│
├── templates/                   ← HTML templates (if Flask)
│   └── index.html
│
├── static/                      ← CSS, JS, images for frontend
│
├── tests/                       ← Unit and integration tests
│   ├── test_quality_agent.py
│   ├── test_price_agent.py
│   ├── test_market_agent.py
│   └── test_decision_agent.py
│
├── notebooks/                   ← Jupyter notebooks for exploration
│   ├── eda_grain_images.ipynb
│   └── eda_price_data.ipynb
│
└── docs/                        ← Documentation
    ├── synopsis.pdf
    ├── architecture_diagram.png
    └── research_paper/
```

---

## 📋 Build Phases (Follow This Order)

### Phase 1 — Project Setup & Data Collection (Week 1)
- [ ] Initialize project structure (folders, requirements.txt, .gitignore, .env)
- [ ] Set up virtual environment (`python -m venv venv`)
- [ ] Download Grain Class Image Dataset and organize into Bajra/Jowar/Ragi folders
- [ ] Scrape/download Agmarknet historical price data (2010-2025)
- [ ] Create `apmc_markets.json` with 20+ markets (name, lat, long, commission_rate)
- [ ] Create `festival_calendar.csv` (date, festival, expected_demand_spike)
- [ ] Create `shelf_life_rules.json`
- [ ] Set up PostgreSQL database schema
- [ ] Get API keys: Google Maps Distance Matrix, OpenWeatherMap/IMD

### Phase 2 — Agent 1: Quality Assessment (Week 2)
- [ ] Build OpenCV preprocessing pipeline (resize 224×224, noise removal, contrast enhancement)
- [ ] Implement blurry image detection (Laplacian variance threshold)
- [ ] Set up data augmentation (rotation, flip, brightness, zoom)
- [ ] Build CNN model with ResNet50 transfer learning
- [ ] Train on grain images (70/15/15 split)
- [ ] Evaluate: target 88-93% type accuracy, 80-85% grade accuracy
- [ ] Create `quality_agent.py` with predict() method returning standard JSON

### Phase 3 — Agent 2: Price Prediction (Week 3-4)
- [ ] Clean Agmarknet data (handle missing values, outliers, normalize)
- [ ] Feature engineering: season, previous_prices, rainfall, temperature, grade
- [ ] Build LSTM model for temporal price patterns
- [ ] Build XGBoost model for feature-based prediction
- [ ] Create ensemble (weighted average or stacking)
- [ ] Train with time-based split (80/10/10)
- [ ] Evaluate: target MAPE 5-15%
- [ ] Create `price_agent.py` that takes Agent 1 output as input

### Phase 4 — Agent 3 & 4: Market + Decision (Week 5-6)
- [ ] Build BeautifulSoup scraper for Agmarknet live APMC prices
- [ ] Integrate Google Maps Distance Matrix API for transport distances
- [ ] Implement transport cost calculation (₹15-25/km/quintal)
- [ ] Create `market_agent.py` with net profit ranking across 20+ APMCs
- [ ] Build decision tree logic in `decision_agent.py`
- [ ] Integrate IMD/OpenWeatherMap API for weather forecasts
- [ ] Implement shelf life calculation from moisture data
- [ ] Add festival calendar demand spike detection
- [ ] Implement cross-agent verification (contradiction detection)

### Phase 5 — Integration & Frontend (Week 7-8)
- [ ] Build Central Orchestrator (`orchestrator.py`) managing agent pipeline
- [ ] Build Streamlit frontend: image upload, results dashboard, recommendations
- [ ] Add Marathi + English language support
- [ ] End-to-end testing: image → quality → price → market → decision → display
- [ ] Error handling: blurry images, scraping failures, API timeouts

### Phase 6 — Testing & Documentation (Week 9)
- [ ] Unit tests for each agent
- [ ] Integration tests for full pipeline
- [ ] Performance benchmarking
- [ ] Write research paper
- [ ] Prepare demo

---

## 🔧 Technology Stack Reference

| Layer | Technology | Version/Notes |
|-------|-----------|---------------|
| **Language** | Python | 3.10+ |
| **Frontend** | Streamlit | Use for proof-of-concept (rapid prototyping) |
| **Image Processing** | OpenCV | Preprocessing, blur detection |
| **Agent 1 (Quality)** | ResNet50 (TensorFlow/Keras) | Transfer learning from ImageNet |
| **Agent 2 (Price)** | LSTM (TensorFlow) + XGBoost | Ensemble model |
| **Agent 3 (Market)** | BeautifulSoup + requests | Agmarknet scraping |
| **Agent 3 (Transport)** | Google Maps Distance Matrix API | Actual road distance |
| **Agent 4 (Decision)** | scikit-learn DecisionTree + rules | Explainable logic |
| **Database** | PostgreSQL | Historical prices, market data |
| **Weather API** | OpenWeatherMap / IMD | 5-day forecasts |
| **ML Libraries** | scikit-learn, Pandas, NumPy, Matplotlib | Standard ML toolkit |
| **Data Augmentation** | TensorFlow ImageDataGenerator | Rotation, flip, brightness, zoom |
| **Agent Communication** | JSON | Via Central Orchestrator |
| **Language Support** | Marathi + English | Farmer-friendly interface |

---

## ⚙️ Claude Code Rules

### General
- Always work from the project root directory
- Follow the project structure above — don't create random files
- Use Python 3.10+ syntax
- Use type hints in all function signatures
- Every agent must have a standardized JSON output format
- Add docstrings to all classes and public methods
- Handle errors gracefully — never let the app crash silently

### Agent Development Pattern
Every agent MUST follow this pattern:
```python
class AgentName:
    def __init__(self, config):
        """Initialize with configuration."""
        pass

    def process(self, input_data: dict) -> dict:
        """
        Main processing method.
        Args: input_data — JSON dict from previous agent or user
        Returns: Standardized JSON dict output
        """
        pass

    def validate_input(self, input_data: dict) -> bool:
        """Validate input before processing."""
        pass
```

### Code Style
- Use `black` for formatting
- Use `flake8` for linting
- Keep functions under 50 lines
- No hardcoded API keys — use `.env` and `python-dotenv`
- Log important events using Python `logging` module
- Write tests alongside code, not after

### Git Commit Convention
```
feat(agent1): add ResNet50 transfer learning pipeline
fix(market): handle Agmarknet scraping timeout
data: add 500 augmented Bajra images
docs: update README with setup instructions
test: add unit tests for price agent
```

### What NOT To Do
- Don't use ChatGPT/LLM APIs as a substitute for actual ML models
- Don't hardcode file paths — use `os.path` or `pathlib`
- Don't skip input validation on any agent
- Don't commit model files (.h5, .pkl) to git — use .gitignore
- Don't commit .env or API keys
- Don't build Flask frontend unless specifically asked — use Streamlit first

---

## 📊 Key Datasets

| Dataset | Source | Size | Use |
|---------|--------|------|-----|
| Grain Class Images | Universe by Vinit (Roboflow) | ~5K raw → 15K+ augmented | Agent 1 training |
| Agmarknet Prices | agmarknet.gov.in | ~50K+ records (2010-2025) | Agent 2 training |
| APMC Markets | Manual compilation | 20+ markets | Agent 3 reference |
| Weather Data | OpenWeatherMap API | Real-time | Agent 4 input |
| Festival Calendar | Manual CSV | ~30 entries/year | Agent 4 input |

---

## 🔑 API Keys Required (.env)

```env
GOOGLE_MAPS_API_KEY=your_key_here
OPENWEATHERMAP_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/milletsaarthi
```

---

## 📚 Key References

1. PMC 2024 — Wheat grain classification with transfer learning (92-95% accuracy)
2. IARJSET 2025 — Grain classification using CNN (90%+ accuracy, ResNet50 best performer)
3. Scientific Reports Jul 2024 — LSTM/GRU price forecasting for agricultural commodities
4. Frontiers Feb 2024 — Hybrid forecasting models combining deep learning + traditional ML
5. eNAM/Agmarknet — Government centralized agricultural market data
6. Scientific Reports Dec 2025 — Real-time agricultural price deployment system
7. ResearchGate Jun 2025 — Multi-agent systems in agriculture (swarm robotics concept applied digitally)

---

## 💡 Key Design Decisions (For Q&A)

**Why multi-agent vs single model?** → Problem is naturally multi-step. Modularity, explainability, error isolation. If price agent fails, quality agent still works.

**Why ResNet50?** → 25M parameters, skip connections, proven best for grain classification (IARJSET 2025).

**Why LSTM + XGBoost ensemble?** → LSTM captures time-series patterns, XGBoost captures non-linear feature relationships. Better together.

**Why Decision Tree in Agent 4?** → (1) Explainability — farmer needs to know WHY, (2) Inputs already processed — not a pattern recognition task, (3) No training data exists for this decision.

**Why not just ChatGPT?** → Can't grade grain from photo, no real-time APMC prices, no Google Maps transport costs, gives generic advice not data-backed recommendations.

---

## 🚀 Quick Start Commands

```bash
# Clone and setup
git clone <repo-url>
cd MilletSaarthi
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run the app
streamlit run app/main.py

# Run tests
pytest tests/ -v

# Train models
python training/train_quality_model.py
python training/train_price_model.py
```

---

*Last updated: February 2026 — Pre-build phase*
