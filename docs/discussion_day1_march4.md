# MilletSaarthi — Day 1 Discussion (March 4, 2026)

## Key Decisions Made

### 1. Agent 1 (Quality Assessment) — Two-Stage Training Approach

**Problem:** We have 1300 images of Ragi, Jowar, and Bajra, but they are NOT labeled by grain type or quality grade.

**Solution — Two-Stage Approach:**

#### Stage 1: Grain Type Classifier (Days 1-4)
1. Manually label the 1300 images into 3 folders: `ragi/`, `jowar/`, `bajra/`
   - This is visual and straightforward
   - Team of 4 can split it and finish in a few hours
2. Train a ResNet50 transfer learning model on these ~430 images/class
   - With augmentation (flip, rotate, brightness), this becomes ~4000+ images
   - Plenty for transfer learning
3. Result: A working "what grain is this?" model

#### Stage 2: Quality Grading (Days 5-8)
1. Click new photos of each grain type showing different quality levels:
   - Grade A: clean, uniform grains
   - Grade B: some broken grains, slight impurities
   - Grade C: broken, discolored, foreign matter visible
2. Even 50-80 photos per grade per grain type (450-720 total) is enough with heavy augmentation + transfer learning from Stage 1
3. Fine-tune the Stage 1 model to also predict grade — or train a separate grade classifier that runs after type is identified

**Why This Works:**
- Stage 1 model gives a working demo fast (type classification)
- Stage 2 builds on top — not starting from scratch
- With ResNet50 transfer learning, even small datasets work well (model already knows visual features from ImageNet)

---

### 2. 25-Day Timeline

| Days  | What                                                  |
|-------|-------------------------------------------------------|
| 1-4   | Label images + Train Type Classifier (Agent 1 v1)    |
| 5-8   | Collect quality photos + Train Grade Classifier (Agent 1 v2) |
| 9-13  | Agent 2 (Price Prediction) + Agent 3 (Market Comparison) |
| 14-18 | Agent 4 (Decision) + Orchestrator + Streamlit UI      |
| 19-22 | Integration testing + bug fixes                        |
| 23-25 | Presentation prep + demo polish                        |

---

### 3. Training Environment

| What                                  | Where               | Why                                    |
|---------------------------------------|----------------------|----------------------------------------|
| Model Training (ResNet50, LSTM, XGBoost) | Google Colab (free GPU) | Laptop can't handle CNN training       |
| App Development (Streamlit, agents, orchestrator) | Local (VS Code) | No GPU needed, just Python logic       |
| Trained Models (.h5, .pkl files)      | Download from Colab -> `models/` folder | Used at inference time locally |

**Colab Workflow:**
1. Upload dataset to Google Drive
2. Open Colab notebook -> mount Drive -> train model
3. Save trained model (.h5 file) to Drive
4. Download .h5 file -> put in local `models/` folder
5. Local app loads the model for predictions

---

### 4. Important Clarification — "Agents" in This Project

Our project is NOT using LLM-based agentic AI (like LangChain/CrewAI). Our "agents" are independent ML modules that pass JSON to each other through an orchestrator. Think of them as microservices, not AI agents. Basic OOP in Python is enough to understand the agent pattern.

---

## Learning Resources

### Transfer Learning with ResNet50 (Agent 1 — Most Important)
- "Transfer Learning with TensorFlow" by freeCodeCamp on YouTube (~1 hour)
- "Image Classification using CNN in Python" by Codebasics on YouTube (Hindi/English)
- TensorFlow official tutorial: https://www.tensorflow.org/tutorials/images/transfer_learning

### LSTM for Time Series (Agent 2)
- "LSTM Time Series Forecasting" by Krish Naik on YouTube (Hindi)
- "Stock Price Prediction using LSTM" by Codebasics on YouTube

### XGBoost (Agent 2)
- "XGBoost Tutorial" by Krish Naik on YouTube

### Streamlit (Frontend)
- "Streamlit Crash Course" by Patrick Loeber on YouTube (30 mins)

---

## Next Steps
- [ ] Team sorts 1300 images into ragi/, jowar/, bajra/ folders
- [ ] Watch Transfer Learning + CNN tutorials
- [ ] Scaffold project structure
- [ ] Build Colab-ready training notebook for Type Classifier
