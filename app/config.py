"""Central config for MilletSaarthi.

Paths match the artifacts produced by the training notebooks and downloaded
locally into ``models/`` and ``data/``.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Agent 1 — EfficientNetB0 grain classifier (Keras .h5)
QUALITY_MODEL_PATH = ROOT / "best_model.h5"
QUALITY_CLASSES_PATH = MODELS_DIR / "classes.json"
IMG_SIZE = 224
QUALITY_CONFIDENCE_THRESHOLD = 0.75

# Agent 2 — XGBoost price model
PRICE_MODEL_PATH = MODELS_DIR / "price_model.json"
PRICE_ENCODERS_PATH = MODELS_DIR / "encoders.pkl"
PRICE_FEATURES_PATH = MODELS_DIR / "features.txt"
PRICE_HISTORY_PATH = DATA_DIR / "master_prices.csv"

# Agent 3 — Market comparison
APMC_MARKETS_PATH = DATA_DIR / "apmc_markets.json"

# Agent 4 — Decision advisor (rule-based, no artifacts)
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Optional API keys
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")
LOCATIONIQ_KEY = os.getenv("LOCATIONIQ_KEY", "")
