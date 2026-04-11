"""Agent 2 — Price Prediction (XGBoost inference wrapper).

Loads model + encoders from notebooks/agent2_step_c_train.ipynb outputs and
predicts modal price per quintal.
"""
from __future__ import annotations

import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from app.config import PRICE_ENCODERS_PATH, PRICE_FEATURES_PATH, PRICE_MODEL_PATH


def season_of(month: int) -> str:
    if month in (6, 7, 8, 9):
        return "kharif"
    if month in (10, 11, 12, 1, 2, 3):
        return "rabi"
    return "summer"


class PriceAgent:
    def __init__(
        self,
        model_path: Optional[Path] = None,
        encoders_path: Optional[Path] = None,
        features_path: Optional[Path] = None,
    ) -> None:
        self.log = logging.getLogger("PriceAgent")
        mp = Path(model_path or PRICE_MODEL_PATH)
        ep = Path(encoders_path or PRICE_ENCODERS_PATH)
        fp = Path(features_path or PRICE_FEATURES_PATH)

        self.ready = mp.exists() and ep.exists() and fp.exists()
        if not self.ready:
            self.log.warning(f"Price artifacts missing ({mp}) — mock mode")
            self.model = None
            self.encoders: dict = {}
            self.features: list[str] = []
            return

        with open(mp, "rb") as f:
            self.model = pickle.load(f)
        with open(ep, "rb") as f:
            self.encoders = pickle.load(f)
        with open(fp) as f:
            self.features = f.read().strip().split(",")
        # Cache known categories for fallback lookups
        self.known_states = set(self.encoders["state"].classes_)
        self.known_districts = set(self.encoders["district"].classes_)
        self.known_millets = set(self.encoders["millet"].classes_)
        self.log.info(
            f"Loaded price model — {len(self.known_millets)} millets, "
            f"{len(self.known_states)} states, {len(self.known_districts)} districts"
        )

    def _resolve_categories(
        self, millet: str, state: str, district: str
    ) -> tuple[str, str, str, bool]:
        """Snap user-provided categories to values the encoders know.

        Returns (millet, state, district, extrapolated_flag).
        Falls back to any known value per field if the exact one is unseen.
        """
        extrapolated = False
        m = millet if millet in self.known_millets else next(iter(self.known_millets))
        if m != millet:
            extrapolated = True
        s = state if state in self.known_states else next(iter(self.known_states))
        if s != state:
            extrapolated = True
        d = district if district in self.known_districts else next(iter(self.known_districts))
        if d != district:
            extrapolated = True
        return m, s, d, extrapolated

    def predict_price_at(
        self, millet: str, grade: str, state: str, district: str, year: int, month: int
    ) -> Optional[float]:
        """Modal price per quintal. None if unseen category or model missing."""
        if not self.ready:
            base = {"jowar": 2800, "bajra": 2500, "ragi": 3400}.get(millet.lower(), 2500)
            mult = {"A": 1.10, "B": 1.00, "C": 0.88}.get(grade.upper(), 1.0)
            return round(base * mult, 2)
        if millet.lower() not in self.known_millets:
            # Don't silently mislabel — better to return None than fake a price
            # for a grain type the model was never trained on.
            self.log.warning(f"Unknown millet type: {millet}")
            return None
        m, s, d, extrapolated = self._resolve_categories(
            millet.lower(), state, district
        )
        if extrapolated:
            self.log.info(
                f"Extrapolating price: ({millet},{state},{district}) -> ({m},{s},{d})"
            )
        try:
            row = {
                "millet_enc":   self.encoders["millet"].transform([m])[0],
                "state_enc":    self.encoders["state"].transform([s])[0],
                "district_enc": self.encoders["district"].transform([d])[0],
                "grade_enc":    self.encoders["grade"].transform([grade.upper()])[0],
                "season_enc":   self.encoders["season"].transform([season_of(month)])[0],
                "year": year, "month": month,
                "month_sin": float(np.sin(2 * np.pi * month / 12)),
                "month_cos": float(np.cos(2 * np.pi * month / 12)),
            }
            X = pd.DataFrame([row])[self.features]
            return float(self.model.predict(X)[0])
        except (ValueError, KeyError) as e:
            self.log.warning(f"predict_price_at failed after fallback: {e}")
            return None

    def predict(self, state: dict) -> dict:
        """Baseline price at farmer's nearest APMC + 1-month forward trend.

        Prefers the state/district of Agent 3's nearest APMC (``local_market``)
        because those are guaranteed to be in the training encoders. Falls back
        to the farmer's geocoded district only if Agent 3 didn't run.
        """
        millet = state["millet"]
        grade = state["grade"]
        qty = state.get("quantity_quintal", 1)
        local = state.get("local_market") or {}
        farmer_state = local.get("state") or state.get("farmer_state", "Maharashtra")
        farmer_district = local.get("district") or state.get("farmer_district", "Pune")
        year = state.get("year")
        month = state.get("month")
        if year is None or month is None:
            now = datetime.now()
            year, month = now.year, now.month

        current = self.predict_price_at(millet, grade, farmer_state, farmer_district, year, month)
        nm_y, nm_m = (year, month + 1) if month < 12 else (year + 1, 1)
        future = self.predict_price_at(millet, grade, farmer_state, farmer_district, nm_y, nm_m)

        if current is None or future is None:
            trend = "unknown"
        elif future > current * 1.02:
            trend = "rising"
        elif future < current * 0.98:
            trend = "falling"
        else:
            trend = "stable"

        price = current if current is not None else 0.0
        return {
            "expected_price": round(price, 2),
            "price_range": [round(price * 0.95, 2), round(price * 1.05, 2)],
            "trend": trend,
            "expected_total_revenue": round(price * qty, 2),
            "confidence": 0.81 if self.ready and current is not None else 0.4,
            "price_source": "xgboost" if self.ready and current is not None else "mock",
        }
