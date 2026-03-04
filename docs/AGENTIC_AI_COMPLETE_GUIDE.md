# MilletSaarthi — Complete Agentic AI Guide

> **Purpose:** This file explains the complete agentic architecture, every technology used, how they connect, learning resources for each, and the full build workflow. Written for team members with zero prior knowledge.

---

## Table of Contents

1. [What is Agentic AI?](#1-what-is-agentic-ai)
2. [Why Our Project is Agentic](#2-why-our-project-is-agentic)
3. [Complete Architecture](#3-complete-architecture)
4. [All 12 Agentic Features](#4-all-12-agentic-features)
5. [Technology Stack (with learning resources)](#5-technology-stack-with-learning-resources)
6. [Complete Build Workflow](#6-complete-build-workflow)
7. [How to Explain in Viva/Presentation](#7-how-to-explain-in-vivapresentation)

---

## 1. What is Agentic AI?

### Simple Definition
Agentic AI = Multiple **independent AI modules (agents)** that can:
- Think on their own (autonomy)
- Talk to each other (communication)
- React to problems (reactivity)
- Remember past actions (memory)
- Heal themselves when something breaks (self-healing)

### It is NOT just:
- A pipeline (A → B → C → D in fixed order)
- A single ML model
- ChatGPT/CrewAI/LangChain (those are LLM-based agents, ours are ML-based agents)

### Academic Definition (Wooldridge & Jennings, 1995):
> "An agent is a computer system that is situated in some environment, and that is capable of autonomous action in this environment in order to meet its design objectives."

4 properties of an intelligent agent:
1. **Autonomy** — operates without direct human intervention
2. **Social ability** — interacts with other agents
3. **Reactivity** — perceives environment and responds
4. **Proactivity** — takes initiative, goal-directed behavior

**Our project satisfies ALL 4.**

---

## 2. Why Our Project is Agentic

| Agentic Property | How MilletSaarthi Implements It |
|---|---|
| **Autonomy** | Each agent independently decides its strategy (live vs cached, retry vs fallback) |
| **Social Ability** | Agents communicate via standardized JSON messages through orchestrator |
| **Reactivity** | System adapts to API failures, bad images, market hours, weather |
| **Proactivity** | Agent 4 detects contradictions and triggers re-verification of other agents |

### Pipeline vs Our Agentic System

```
PIPELINE (not agentic):
  Image → Agent1 → Agent2 → Agent3 → Agent4 → Output
  (fixed path, no decisions, no feedback, no recovery)

OUR AGENTIC SYSTEM:
  ┌──────────────────────────────────────────┐
  │           SMART ORCHESTRATOR             │
  │  - Decides which agent to call           │
  │  - Monitors agent health                 │
  │  - Handles failures & retries            │
  │  - Runs agents in parallel when possible │
  │  - Manages agent registration            │
  └──┬─────┬──────┬──────┬──────────────────┘
     │     │      │      │         ▲ ▲ ▲
     ▼     ▼      ▼      ▼         │ │ │ (feedback)
  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
  │ A1   │ │ A2   │ │ A3   │ │ A4   │
  │Qualit│ │Price │ │Market│ │Decis.│
  ├──────┤ ├──────┤ ├──────┤ ├──────┤
  │Memory│ │Memory│ │Memory│ │Memory│
  │State │ │State │ │State │ │State │
  └──────┘ └──────┘ └──────┘ └──────┘
     │          │        │        │
     └───── communicate back ─────┘
```

---

## 3. Complete Architecture

### System Flow (How a farmer request works)

```
FARMER opens app
  │
  ├── Uploads grain image
  ├── Enters location (city/village name)
  ├── Enters quantity (in quintals)
  │
  ▼
┌──────────────────────────────────────────────────────────┐
│                   SMART ORCHESTRATOR                     │
│                                                          │
│  Step 1: Check environment                               │
│    - Is Agmarknet website up?                            │
│    - Is weather API responding?                          │
│    - Is it market hours?                                 │
│    - Set agent modes accordingly                         │
│                                                          │
│  Step 2: Run Agent 1 (Quality)                           │
│    - Send image to Quality Agent                         │
│    - IF confidence < 0.4 → ask farmer to retake image    │
│    - IF confidence < 0.7 → continue but flag as LOW      │
│    - IF confident → continue normally                    │
│                                                          │
│  Step 3: Run Agent 2 + Agent 3 IN PARALLEL               │
│    - Price Agent predicts price (needs Agent 1 output)   │
│    - Market Agent finds best markets (can start early)   │
│    - Both run at the same time (parallel execution)      │
│                                                          │
│  Step 4: Run Agent 4 (Decision)                          │
│    - Gets ALL results from Agent 1, 2, 3                 │
│    - Checks weather, shelf life, festivals               │
│    - Makes SELL_NOW / HOLD / SELL_LATER decision         │
│                                                          │
│  Step 5: Verification loop                               │
│    - IF Agent 4 finds contradictions:                    │
│      → Re-run Agent 2 with adjusted params               │
│      → Re-run Agent 4 with new data                      │
│    - IF still contradictions after retry:                 │
│      → Flag warnings to farmer                           │
│                                                          │
│  Step 6: Compile and return final result                  │
│    - Combine all agent outputs                           │
│    - Add confidence scores                               │
│    - Add any warnings                                    │
│    - Display on Streamlit UI                             │
└──────────────────────────────────────────────────────────┘
```

### Agent Communication Flow (JSON Messages)

```
Agent 1 Output:
{
  "sender": "quality_agent",
  "type": "RESULT",
  "confidence": 0.89,
  "payload": {
    "millet": "Bajra",
    "grade": "A",
    "quality_score": 0.87
  }
}
        │
        ▼
Agent 2 Output:
{
  "sender": "price_agent",
  "type": "RESULT",
  "confidence": 0.81,
  "payload": {
    "expected_price": 3150,
    "trend": "rising",
    "price_range": {"min": 2900, "max": 3400}
  }
}
        │
        ▼
Agent 3 Output:
{
  "sender": "market_agent",
  "type": "RESULT",
  "confidence": 0.95,
  "payload": {
    "best_market": "Aurangabad APMC",
    "net_profit": 3020,
    "distance_km": 38,
    "strategy_used": "LIVE",
    "top_markets": [...]
  }
}
        │
        ▼
Agent 4 Output:
{
  "sender": "decision_agent",
  "type": "RESULT",
  "confidence": 0.85,
  "payload": {
    "action": "SELL_NOW",
    "market": "Aurangabad APMC",
    "reason": "Rain forecast in 3 days + good price trend",
    "risk_level": "LOW",
    "contradictions": [],
    "warnings": []
  }
}
```

---

## 4. All 12 Agentic Features

### Feature 1: Smart Routing
**What:** Orchestrator decides which path to take based on situation.
**Example:** If grain is Grade C with high moisture → skip detailed market comparison, just recommend nearest market urgently.

### Feature 2: Feedback Loops
**What:** Agent 4 can tell the orchestrator to re-run earlier agents.
**Example:** Agent 4 detects Grade A grain but very low price prediction → asks Agent 2 to recheck.

### Feature 3: Agent Autonomy
**What:** Each agent decides its own strategy independently.
**Example:** Market Agent tries live scraping, if it fails, autonomously switches to cached/predicted prices.

### Feature 4: Goal Evaluation
**What:** Agents check if their own output is good enough.
**Example:** Quality Agent confidence is 0.35 → returns "NEED_HELP" instead of a bad result.

### Feature 5: Inter-Agent Communication
**What:** Agents can send messages forward AND backward through the orchestrator.
**Example:** Decision Agent sends a "RETRY_REQUEST" message back to Price Agent.

### Feature 6: Agent Memory
**What:** Agents remember results from previous runs.
**Example:** Price Agent remembers last 10 predictions. If current prediction is wildly different, it flags it as suspicious.

### Feature 7: Environment Awareness
**What:** System checks external conditions before running.
**Example:** Agmarknet website is down → Market Agent switches to offline mode automatically.

### Feature 8: Agent Registration & Discovery
**What:** Agents register themselves with the orchestrator. Orchestrator doesn't hardcode agent names.
**Example:** You can add a 5th agent later without changing orchestrator code — just register it.

### Feature 9: Health Monitoring & Self-Healing
**What:** Orchestrator tracks agent failures and auto-recovers.
**Example:** If Market Agent fails 3 times in a row, orchestrator marks it as unhealthy and uses fallback.

### Feature 10: Confidence-Based Delegation
**What:** Agents report how confident they are. Low confidence triggers special handling.
**Example:** Quality Agent is only 50% sure → orchestrator shows result with a warning to farmer.

### Feature 11: Parallel Execution
**What:** Independent agents run at the same time.
**Example:** Price Agent and Market Agent run in parallel (both only need Agent 1 output).

### Feature 12: Standardized Message Protocol
**What:** All agents use the same message format (sender, receiver, type, payload, confidence, timestamp).
**Example:** Every message has a "type" field — RESULT, ERROR, NEED_HELP, RETRY_REQUEST — so orchestrator knows how to handle it.

---

## 5. Technology Stack (with Learning Resources)

### 5.1 Python (Core Language)
**Used for:** Everything — all agents, orchestrator, frontend
**Version:** 3.10+

| Resource | Type | Link |
|---|---|---|
| Python Full Course (Hindi) | YouTube | Search: "Python Full Course for Beginners CodeWithHarry" |
| Python OOP Tutorial | YouTube | Search: "Python OOP Tutorial Corey Schafer" |
| Python Official Tutorial | Docs | https://docs.python.org/3/tutorial/ |

**Key concepts needed:** Classes, inheritance, abstract classes, dictionaries, exception handling, type hints

---

### 5.2 TensorFlow / Keras (Agent 1: Quality Model)
**Used for:** ResNet50 transfer learning for grain image classification
**What it does:** Takes a grain image → outputs grain type (Bajra/Jowar/Ragi) + grade (A/B/C)

| Resource | Type | Link |
|---|---|---|
| Transfer Learning with TensorFlow | YouTube | Search: "Transfer Learning TensorFlow freeCodeCamp" (~1 hr) |
| Image Classification CNN (Hindi) | YouTube | Search: "Image Classification using CNN Python Codebasics" |
| Keras ResNet50 Guide | YouTube | Search: "ResNet50 Transfer Learning Keras tutorial" |
| TensorFlow Official Tutorial | Docs | https://www.tensorflow.org/tutorials/images/transfer_learning |

**Key concepts needed:**
- What is a CNN (Convolutional Neural Network)
- What is transfer learning (using a pre-trained model)
- What is ResNet50 (a specific pre-trained CNN architecture)
- How to freeze/unfreeze layers
- How to add custom classification layers on top
- Train/validation/test split

**How it fits in our project:**
```
Farmer image → OpenCV preprocessing → ResNet50 model → {millet: "Bajra", grade: "A", confidence: 0.89}
```

---

### 5.3 OpenCV (Image Preprocessing)
**Used for:** Preprocessing grain images before feeding to the CNN model
**What it does:** Resize, denoise, enhance contrast, detect blurry images

| Resource | Type | Link |
|---|---|---|
| OpenCV Python Course (Hindi) | YouTube | Search: "OpenCV Python Tutorial for Beginners Codebasics" |
| OpenCV Crash Course | YouTube | Search: "OpenCV Course freeCodeCamp" |
| OpenCV Official Docs | Docs | https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html |

**Key concepts needed:**
- Resize images (cv2.resize)
- Convert color spaces (cv2.cvtColor)
- Gaussian blur / denoise (cv2.GaussianBlur)
- CLAHE contrast enhancement
- Laplacian variance (blur detection)

---

### 5.4 LSTM — Long Short-Term Memory (Agent 2: Price Model)
**Used for:** Time-series price prediction — learns patterns from historical prices
**What it does:** Looks at last 30 days of prices → predicts tomorrow's price

| Resource | Type | Link |
|---|---|---|
| LSTM Time Series (Hindi) | YouTube | Search: "LSTM Time Series Forecasting Krish Naik" |
| Stock Price Prediction LSTM | YouTube | Search: "Stock Price Prediction LSTM Codebasics" |
| LSTM Explained Simply | YouTube | Search: "LSTM Networks Explained StatQuest" |
| TensorFlow LSTM Tutorial | Docs | https://www.tensorflow.org/tutorials/structured_data/time_series |

**Key concepts needed:**
- What is a time series (data ordered by time)
- What is an RNN (Recurrent Neural Network)
- What is LSTM (improved RNN that remembers long patterns)
- Sequence length (how many past days to look at)
- How to shape data for LSTM (samples, timesteps, features)

---

### 5.5 XGBoost (Agent 2: Price Model — Ensemble Partner)
**Used for:** Feature-based price prediction using tabular data
**What it does:** Takes features (season, grade, market, previous prices) → predicts price

| Resource | Type | Link |
|---|---|---|
| XGBoost Tutorial (Hindi) | YouTube | Search: "XGBoost Tutorial Krish Naik" |
| XGBoost Explained | YouTube | Search: "XGBoost StatQuest" (best explanation) |
| XGBoost Official Docs | Docs | https://xgboost.readthedocs.io/ |

**Key concepts needed:**
- What is gradient boosting (builds many small trees, each fixing previous errors)
- What is XGBoost (fast implementation of gradient boosting)
- Feature engineering (creating useful input columns)
- Hyperparameter tuning (n_estimators, max_depth, learning_rate)

**Why LSTM + XGBoost together (Ensemble):**
```
LSTM captures:  "prices have been rising for 2 weeks" (temporal patterns)
XGBoost captures: "Bajra Grade A in winter at Nagpur APMC" (feature relationships)

Ensemble = 0.6 × LSTM prediction + 0.4 × XGBoost prediction = better prediction
```

---

### 5.6 scikit-learn (Agent 4: Decision Tree + Utilities)
**Used for:** Decision tree in Agent 4, data preprocessing utilities, train/test splitting

| Resource | Type | Link |
|---|---|---|
| scikit-learn Crash Course | YouTube | Search: "Scikit-learn Tutorial freeCodeCamp" |
| Decision Tree (Hindi) | YouTube | Search: "Decision Tree Krish Naik Hindi" |
| Decision Tree Explained | YouTube | Search: "Decision Tree StatQuest" |
| scikit-learn Official Docs | Docs | https://scikit-learn.org/stable/tutorial/ |

**Key concepts needed:**
- train_test_split
- Decision trees (if-else learned from data)
- StandardScaler / MinMaxScaler
- Classification vs Regression

---

### 5.7 Pandas & NumPy (Data Handling)
**Used for:** Loading CSVs, cleaning data, feature engineering, array operations

| Resource | Type | Link |
|---|---|---|
| Pandas Complete Course (Hindi) | YouTube | Search: "Pandas Tutorial Codebasics Hindi" |
| NumPy Tutorial | YouTube | Search: "NumPy Tutorial freeCodeCamp" |
| Pandas Official Docs | Docs | https://pandas.pydata.org/docs/getting_started/ |

**Key concepts needed:**
- DataFrames (like Excel sheets in Python)
- Reading CSVs (pd.read_csv)
- Handling missing values (fillna, dropna)
- Feature engineering (creating new columns)
- Merging datasets

---

### 5.8 BeautifulSoup + Requests (Agent 3: Web Scraping)
**Used for:** Scraping live APMC prices from Agmarknet website

| Resource | Type | Link |
|---|---|---|
| Web Scraping (Hindi) | YouTube | Search: "Web Scraping Python Codebasics Hindi" |
| BeautifulSoup Tutorial | YouTube | Search: "BeautifulSoup Web Scraping freeCodeCamp" |
| Requests Library | Docs | https://docs.python-requests.org/ |
| BeautifulSoup Docs | Docs | https://www.crummy.com/software/BeautifulSoup/bs4/doc/ |

**Key concepts needed:**
- HTTP requests (GET/POST)
- HTML structure (tags, classes, IDs)
- Parsing HTML with BeautifulSoup
- Extracting data from tables
- Error handling (website down, timeout)

---

### 5.9 Google Maps Distance Matrix API (Agent 3: Transport)
**Used for:** Calculating road distance between farmer location and APMC markets

| Resource | Type | Link |
|---|---|---|
| Google Maps API Python | YouTube | Search: "Google Maps API Python Tutorial" |
| googlemaps Python Library | Docs | https://github.com/googlemaps/google-maps-services-python |
| Distance Matrix API Docs | Docs | https://developers.google.com/maps/documentation/distance-matrix |

**Key concepts needed:**
- Getting an API key from Google Cloud Console
- Making API calls with the googlemaps Python library
- Understanding response format (distance, duration)
- Rate limiting and caching

---

### 5.10 OpenWeatherMap API (Agent 4: Weather)
**Used for:** Getting 5-day weather forecast for farmer's location

| Resource | Type | Link |
|---|---|---|
| OpenWeatherMap API Tutorial | YouTube | Search: "OpenWeatherMap API Python tutorial" |
| API Docs | Docs | https://openweathermap.org/forecast5 |

**Key concepts needed:**
- Free API key signup
- Making GET requests with API key
- Parsing JSON response
- Extracting rain/storm forecasts

---

### 5.11 Streamlit (Frontend UI)
**Used for:** Building the farmer-facing web app

| Resource | Type | Link |
|---|---|---|
| Streamlit Crash Course | YouTube | Search: "Streamlit Crash Course Patrick Loeber" (30 mins) |
| Streamlit for ML Apps (Hindi) | YouTube | Search: "Streamlit Tutorial Hindi Krish Naik" |
| Streamlit Official Docs | Docs | https://docs.streamlit.io/ |

**Key concepts needed:**
- st.file_uploader (image upload)
- st.text_input, st.number_input (farmer inputs)
- st.columns, st.expander (layout)
- st.spinner (loading state)
- st.success, st.warning, st.error (status messages)
- Session state (maintaining data across reruns)

---

### 5.12 PostgreSQL + SQLAlchemy (Database)
**Used for:** Storing historical prices, market data, past predictions

| Resource | Type | Link |
|---|---|---|
| PostgreSQL Tutorial (Hindi) | YouTube | Search: "PostgreSQL Tutorial Hindi" |
| SQLAlchemy ORM Tutorial | YouTube | Search: "SQLAlchemy Python Tutorial" |
| PostgreSQL Docs | Docs | https://www.postgresql.org/docs/ |

**Key concepts needed:**
- CREATE TABLE, INSERT, SELECT
- SQLAlchemy ORM (Python objects ↔ database rows)
- Connection strings
- Basic queries

---

### 5.13 Python Threading (Parallel Execution)
**Used for:** Running Agent 2 and Agent 3 in parallel

| Resource | Type | Link |
|---|---|---|
| Python Threading Tutorial | YouTube | Search: "Python Threading Tutorial Corey Schafer" |
| concurrent.futures | YouTube | Search: "Python concurrent.futures tutorial" |
| Official Docs | Docs | https://docs.python.org/3/library/concurrent.futures.html |

**Key concepts needed:**
- ThreadPoolExecutor
- executor.submit() and future.result()
- When to use threading vs multiprocessing

---

### 5.14 Python OOP — Abstract Classes (Agent Pattern)
**Used for:** BaseAgent class that all agents inherit from

| Resource | Type | Link |
|---|---|---|
| Abstract Classes Python | YouTube | Search: "Python Abstract Classes Tutorial Corey Schafer" |
| ABC module | YouTube | Search: "Python ABC abstractmethod tutorial" |

**Key concepts needed:**
- ABC (Abstract Base Class)
- @abstractmethod decorator
- Inheritance
- Why we use it (enforces consistent interface across all agents)

---

### 5.15 Python Logging (Observability)
**Used for:** Logging agent inputs, outputs, decisions, errors

| Resource | Type | Link |
|---|---|---|
| Python Logging | YouTube | Search: "Python Logging Tutorial Corey Schafer" |
| Loguru Library | Docs | https://github.com/Delgan/loguru |

---

### 5.16 Google Colab (Training Environment)
**Used for:** Training CNN and LSTM models (free GPU)

| Resource | Type | Link |
|---|---|---|
| Google Colab Tutorial | YouTube | Search: "Google Colab Tutorial for Beginners" |
| Colab + TensorFlow | YouTube | Search: "TensorFlow Google Colab GPU tutorial" |

**Workflow:**
```
1. Upload dataset to Google Drive
2. Open Colab notebook → mount Drive → train model
3. Save trained model (.h5 / .pkl) to Drive
4. Download model → put in local models/ folder
5. Local app loads model for predictions
```

---

### 5.17 pytest (Testing)
**Used for:** Testing each agent and the full pipeline

| Resource | Type | Link |
|---|---|---|
| Pytest Tutorial | YouTube | Search: "Pytest Tutorial for Beginners" |
| Pytest Official Docs | Docs | https://docs.pytest.org/ |

---

## 6. Complete Build Workflow

### Phase 1: Learn Prerequisites (Days 1-5)
**Everyone must complete:**

| Day | What to Learn | Resources |
|---|---|---|
| Day 1 | Python OOP (classes, inheritance, abstract classes) | Corey Schafer OOP playlist |
| Day 2 | What is CNN, Transfer Learning, ResNet50 (watch only) | freeCodeCamp Transfer Learning |
| Day 3 | What is LSTM, Time Series (watch only) | Krish Naik LSTM video |
| Day 4 | What is XGBoost, Decision Tree (watch only) | StatQuest XGBoost + Decision Tree |
| Day 5 | Streamlit basics (try building a simple app) | Patrick Loeber Crash Course |

**You don't need to master these.** Just understand what each thing does and how to use it with code examples.

---

### Phase 2: Project Foundation (Days 6-8)

```
Step 2.1  Create complete folder structure (see WORKFLOW.md)
Step 2.2  Create requirements.txt
Step 2.3  Create .gitignore, .env.example
Step 2.4  Create app/config.py — all constants, paths, thresholds
Step 2.5  Create app/utils.py — logging setup, JSON validators

Step 2.6  Create AgentMessage class (standardized protocol)
          File: agents/message.py
          - sender, receiver, msg_type, payload, confidence, timestamp

Step 2.7  Create BaseAgent abstract class
          File: agents/base_agent.py
          - abstract process() method
          - abstract validate_input() method
          - abstract fallback() method        ← NEW (agentic)
          - memory list (past results)        ← NEW (agentic)
          - health status tracking            ← NEW (agentic)

Step 2.8  Create Smart Orchestrator skeleton
          File: app/orchestrator.py
          - Agent registration system         ← NEW (agentic)
          - Environment checker               ← NEW (agentic)
          - Health monitor                    ← NEW (agentic)
          - Smart routing logic               ← NEW (agentic)
          - Feedback loop handler             ← NEW (agentic)
          - Parallel execution support        ← NEW (agentic)

Step 2.9  Create static data files
          - data/apmc_markets.json
          - data/festival_calendar.csv
          - data/shelf_life_rules.json

Step 2.10 Git commit: "feat: initialize agentic architecture with base classes"
```

---

### Phase 3: Agent 1 — Quality Assessment (Days 9-16)

```
Step 3.1  Manually sort 1300 images into bajra/, jowar/, ragi/ folders
          (Team divides work — ~325 images per person)

Step 3.2  Build preprocessing/image_preprocessor.py
          - Resize to 224x224
          - Gaussian denoise
          - CLAHE contrast enhancement
          - Laplacian blur detection

Step 3.3  Build preprocessing/augmentation.py
          - Rotation, flip, brightness, zoom
          - 1300 raw → 5000+ augmented

Step 3.4  Build training/train_quality_model.py (run on Colab)
          - ResNet50 transfer learning
          - Stage 1: Type classification (Bajra/Jowar/Ragi)
          - Stage 2: Grade classification (A/B/C)

Step 3.5  Build agents/quality_agent.py (AGENTIC version)
          - Inherits from BaseAgent
          - process() returns AgentMessage
          - Confidence-based delegation:
            < 0.4 → NEED_HELP
            < 0.7 → LOW_CONFIDENCE
            >= 0.7 → CONFIDENT
          - fallback() → returns "unable to classify, try another image"
          - Memory: stores last 10 predictions
          - Auto-registers with orchestrator

Step 3.6  Build tests/test_quality_agent.py

Step 3.7  Git commit: "feat(agent1): agentic quality assessment with confidence delegation"
```

---

### Phase 4: Agent 2 — Price Prediction (Days 17-26)

```
Step 4.1  Download Agmarknet data → data/agmarknet/raw/

Step 4.2  Build preprocessing/price_data_cleaner.py
          - Handle missing values
          - Remove outliers
          - Feature engineering (season, lags, rolling mean)

Step 4.3  Build training/train_price_model.py (run on Colab)
          - LSTM for temporal patterns
          - XGBoost for feature patterns
          - Ensemble: 0.6 LSTM + 0.4 XGBoost

Step 4.4  Build agents/price_agent.py (AGENTIC version)
          - Inherits from BaseAgent
          - process() returns AgentMessage
          - Memory: remembers last 10 predictions
            If new prediction differs > 500 from history → flag as suspicious
          - Handles RETRY_REQUEST from Agent 4
          - fallback() → returns MSP (minimum support price) as safe estimate
          - Auto-registers with orchestrator

Step 4.5  Build tests/test_price_agent.py

Step 4.6  Git commit: "feat(agent2): agentic price prediction with memory and retry support"
```

---

### Phase 5: Agent 3 — Market Comparison (Days 27-33)

```
Step 5.1  Build agents/market_agent.py (AGENTIC version)
          - Inherits from BaseAgent
          - Autonomous strategy selection:
            Strategy 1: LIVE (scrape real-time prices)
            Strategy 2: CACHED (use last cached prices)
            Strategy 3: PREDICTED (use Agent 2 prediction)
            Strategy 4: EXPANDED (wider search radius)
          - Agent decides strategy autonomously based on conditions
          - Google Maps API for distance calculation
          - Transport cost = distance × rate × quantity
          - Net profit = market_price × quantity - transport - commission
          - Rank top 5 markets by net profit
          - fallback() → return 3 nearest markets with predicted prices
          - Memory: caches API responses for 1 hour
          - Auto-registers with orchestrator

Step 5.2  Build tests/test_market_agent.py (with mocked APIs)

Step 5.3  Git commit: "feat(agent3): agentic market comparison with autonomous strategy"
```

---

### Phase 6: Agent 4 — Decision Advisor (Days 34-40)

```
Step 6.1  Build agents/decision_agent.py (AGENTIC version)
          - Inherits from BaseAgent
          - Weather check (OpenWeatherMap API)
          - Shelf life check (moisture → days until spoilage)
          - Festival check (upcoming demand spikes)
          - Price trend check (from Agent 2)

          Decision logic (priority order):
            1. moisture > 14% → SELL_NOW (urgent)
            2. Rain in 3 days + outdoor storage → SELL_NOW
            3. Festival in 7 days + price rising → HOLD
            4. Price falling + no festival → SELL_NOW
            5. Default → SELL_NOW at best market

          Contradiction detection (AGENTIC):
            - Grade A but price < MSP → flag
            - Agent 2 says rising but live prices falling → flag
            - Distance > 200km → high transport risk
            IF contradictions found → send RETRY_REQUEST back to orchestrator

          Goal evaluation (AGENTIC):
            - If confidence < 0.5 → return NEED_MORE_DATA
            - Tells orchestrator what's missing

          - fallback() → return SELL_NOW at nearest market (safe default)
          - Memory: stores past decisions for pattern learning
          - Auto-registers with orchestrator

Step 6.2  Build tests/test_decision_agent.py

Step 6.3  Git commit: "feat(agent4): agentic decision advisor with contradiction detection"
```

---

### Phase 7: Smart Orchestrator (Days 41-47)

```
Step 7.1  Complete app/orchestrator.py (THE BRAIN)

          Agent Registration:
            - register_agent(name, instance, dependencies)
            - resolve_execution_order() — topological sort
            - No hardcoded agent names

          Environment Check:
            - check_agmarknet_status()
            - check_weather_api_status()
            - check_market_hours()
            - Set agent modes based on environment

          Smart Routing:
            - Normal path: A1 → (A2 || A3) → A4
            - Urgent path: A1 → A4 (skip A2, A3)
            - Low confidence path: A1 → ask farmer → retry
            - Offline path: A1 → A2 → A4 (skip A3 scraping)

          Parallel Execution:
            - Use ThreadPoolExecutor
            - Run A2 and A3 in parallel after A1

          Feedback Loop:
            - If A4 returns contradictions → re-run A2 → re-run A4
            - Max 2 retry rounds (prevent infinite loops)

          Health Monitoring:
            - Track consecutive failures per agent
            - If agent fails 3x → switch to fallback mode
            - Log all agent response times

          Compile Final Output:
            - Merge all agent results
            - Add overall confidence
            - Add warnings and contradictions
            - Return single JSON to frontend

Step 7.2  Build tests/test_orchestrator.py
          - Test normal flow
          - Test urgent flow
          - Test agent failure recovery
          - Test feedback loop
          - Test parallel execution

Step 7.3  Git commit: "feat(orchestrator): smart orchestrator with all agentic features"
```

---

### Phase 8: Frontend — Streamlit UI (Days 48-54)

```
Step 8.1  Build app/main.py (Streamlit)
          Page 1 — Input:
            - Image uploader
            - Location input (text)
            - Quantity input (number)
            - Submit button

          Page 2 — Results Dashboard:
            - Quality card (grain type, grade, confidence, image preview)
            - Price card (expected price, trend, confidence)
            - Market card (top 3 markets table with distance, net profit)
            - Decision card (action, reason, risk level)
            - Warnings section (any contradictions or low confidence flags)

          - Loading spinners per agent (show pipeline progress)
          - Language toggle: English / Marathi
          - Error states: blurry image, API timeout, agent failure

Step 8.2  Git commit: "feat(ui): Streamlit frontend with bilingual support"
```

---

### Phase 9: Integration Testing & Polish (Days 55-60)

```
Step 9.1  End-to-end test with 10+ images
Step 9.2  Test all agentic paths (normal, urgent, retry, fallback)
Step 9.3  Performance benchmarking
Step 9.4  Fix bugs
Step 9.5  Write README.md
Step 9.6  Create architecture diagram
Step 9.7  Prepare demo
Step 9.8  Git tag: "v1.0.0"
```

---

## 7. How to Explain in Viva/Presentation

### One-liner:
> "MilletSaarthi is a Multi-Agent Intelligence System where four autonomous AI agents collaborate through a smart orchestrator to help millet farmers make optimal selling decisions."

### When asked "What makes it agentic?":
> "Our system implements all four properties of intelligent agents as defined by Wooldridge & Jennings (1995):
> 1. **Autonomy** — each agent independently selects its strategy (live scraping vs cached data, retry vs fallback)
> 2. **Social ability** — agents communicate via standardized JSON messages and can request re-verification from each other
> 3. **Reactivity** — the system adapts to external conditions like API failures, market hours, and weather changes
> 4. **Proactivity** — the decision agent detects contradictions and initiates re-runs of other agents to improve accuracy"

### When asked "Why not CrewAI/LangChain?":
> "CrewAI uses LLMs (like GPT) as the brain of each agent. Our problem requires specialized ML models — a CNN for image classification, LSTM for time-series prediction — that LLMs cannot replace. We implemented the multi-agent pattern from scratch using domain-specific intelligence, which is more accurate, cheaper (no API costs), and more explainable for farmers."

### Key references to cite:
- Wooldridge & Jennings (1995) — "Intelligent Agents: Theory and Practice"
- Russell & Norvig — "Artificial Intelligence: A Modern Approach" (Chapter on Multi-Agent Systems)
- Your own architecture diagram showing all 12 agentic features

---

## Learning Priority (Start Here)

If you're overwhelmed, follow this exact order:

| Priority | What | Time | Why |
|---|---|---|---|
| 1 | Python OOP (classes, inheritance) | 2 hours | Everything is built on this |
| 2 | Watch CNN / Transfer Learning video | 1 hour | Understand Agent 1 |
| 3 | Watch LSTM video | 1 hour | Understand Agent 2 |
| 4 | Try Streamlit tutorial | 30 mins | See how the UI works |
| 5 | Watch XGBoost video | 30 mins | Understand Agent 2 ensemble |
| 6 | Read BeautifulSoup tutorial | 30 mins | Understand Agent 3 |
| 7 | Watch Decision Tree video | 30 mins | Understand Agent 4 |

**Total: ~6 hours to understand everything at a basic level.**

You do NOT need to be an expert in any of these. You need to understand what they do and how to use them with code examples. Claude Code will help you write the actual implementation.

---

*Last updated: March 4, 2026*
*Project: MilletSaarthi — Group 7, Section B, VI Semester AIML, RCOEM*
