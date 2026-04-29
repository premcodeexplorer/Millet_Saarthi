"""Agent 2 — Price Prediction (XGBoost inference wrapper, v3 with lag features).

Loads model + encoders from notebooks/agent2_step_c_train.ipynb outputs and
predicts modal price per quintal.

The trained model expects 11 features including lag_1m / lag_12m /
rolling_3m_mean, which are looked up from master_prices.csv at inference time.
Grade adjustment is applied as a post-prediction multiplier — the model itself
predicts the grade-agnostic BASE price.
"""
from __future__ import annotations

import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import xgboost as xgb

from app.config import (
    PRICE_ENCODERS_PATH,
    PRICE_FEATURES_PATH,
    PRICE_HISTORY_PATH,
    PRICE_MODEL_PATH,
)


GRADE_MULTIPLIER = {"A": 1.10, "B": 1.00, "C": 0.88}


def season_of(month: int) -> str:
    if month in (6, 7, 8, 9):
        return "kharif"
    if month in (10, 11, 12, 1, 2, 3):
        return "rabi"
    return "summer"


def _date_idx(year: int, month: int) -> int:
    return year * 12 + month


class PriceAgent:
    def __init__(
        self,
        model_path: Optional[Path] = None,
        encoders_path: Optional[Path] = None,
        features_path: Optional[Path] = None,
        history_path: Optional[Path] = None,
    ) -> None:
        self.log = logging.getLogger("PriceAgent")
        mp = Path(model_path or PRICE_MODEL_PATH)
        ep = Path(encoders_path or PRICE_ENCODERS_PATH)
        fp = Path(features_path or PRICE_FEATURES_PATH)
        hp = Path(history_path or PRICE_HISTORY_PATH)

        self.ready = mp.exists() and ep.exists() and fp.exists() and hp.exists()
        if not self.ready:
            missing = [str(p) for p in (mp, ep, fp, hp) if not p.exists()]
            self.log.warning(f"Price artifacts missing ({missing}) — mock mode")
            self.model = None
            self.encoders: dict = {}
            self.features: list[str] = []
            self.price_history: dict = {}
            return

        # Load via XGBoost's portable JSON format — pickled .pkl models do not
        # round-trip across XGBoost versions and silently produce garbage
        # predictions (negative prices). JSON is the officially supported
        # cross-version format.
        self.model = xgb.XGBRegressor()
        self.model.load_model(str(mp))
        with open(ep, "rb") as f:
            self.encoders = pickle.load(f)
        with open(fp) as f:
            self.features = f.read().strip().split(",")

        self.known_states = set(self.encoders["state"].classes_)
        self.known_districts = set(self.encoders["district"].classes_)
        self.known_millets = set(self.encoders["millet"].classes_)

        hist = pd.read_csv(hp)
        hist["date_idx"] = hist["year"] * 12 + hist["month"]
        hist = hist.sort_values(["millet", "state", "district", "date_idx"])
        self.price_history = {
            key: grp[["date_idx", "modal_price"]].reset_index(drop=True)
            for key, grp in hist.groupby(["millet", "state", "district"])
        }

        self.log.info(
            f"Loaded price model — {len(self.known_millets)} millets, "
            f"{len(self.known_states)} states, {len(self.known_districts)} districts, "
            f"{len(self.price_history)} (millet,state,district) groups in history"
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

    def _get_lag_features(
        self, millet: str, state: str, district: str, year: int, month: int
    ) -> Optional[dict]:
        """Look up lag_1m / lag_12m / rolling_3m_mean from price history.

        Returns None if no history exists for the (millet, state, district) key.
        Missing individual lags fall back to the group's mean price so the
        model gets values in a sensible magnitude rather than zeros.
        """
        hist = self.price_history.get((millet, state, district))
        if hist is None or len(hist) == 0:
            return None

        target = _date_idx(year, month)
        prices = hist["modal_price"].to_numpy()
        idxs = hist["date_idx"].to_numpy()

        def at(idx: int) -> Optional[float]:
            mask = idxs == idx
            if mask.any():
                return float(prices[mask][0])
            before = idxs < idx
            if before.any():
                return float(prices[before][-1])
            return None

        lag_1m = at(target - 1)
        lag_12m = at(target - 12)

        window_mask = (idxs >= target - 3) & (idxs <= target - 1)
        rolling = float(prices[window_mask].mean()) if window_mask.any() else None

        group_mean = float(prices.mean())
        return {
            "lag_1m": lag_1m if lag_1m is not None else group_mean,
            "lag_12m": lag_12m if lag_12m is not None else group_mean,
            "rolling_3m_mean": rolling if rolling is not None else group_mean,
        }

    def predict_price_at(
        self, millet: str, grade: str, state: str, district: str, year: int, month: int
    ) -> Optional[float]:
        """Modal price per quintal (grade-adjusted). None if unseen category or
        model missing."""
        if not self.ready:
            base = {"jowar": 2800, "bajra": 2500, "ragi": 3400}.get(millet.lower(), 2500)
            mult = GRADE_MULTIPLIER.get(grade.upper(), 1.0)
            return round(base * mult, 2)
        if millet.lower() not in self.known_millets:
            self.log.warning(f"Unknown millet type: {millet}")
            return None
        m, s, d, extrapolated = self._resolve_categories(
            millet.lower(), state, district
        )
        if extrapolated:
            self.log.info(
                f"Extrapolating price: ({millet},{state},{district}) -> ({m},{s},{d})"
            )
        lags = self._get_lag_features(m, s, d, year, month)
        if lags is None:
            self.log.warning(f"No price history for ({m},{s},{d}) — cannot predict")
            return None
        try:
            row = {
                "millet_enc":   self.encoders["millet"].transform([m])[0],
                "state_enc":    self.encoders["state"].transform([s])[0],
                "district_enc": self.encoders["district"].transform([d])[0],
                "season_enc":   self.encoders["season"].transform([season_of(month)])[0],
                "year": year, "month": month,
                "month_sin": float(np.sin(2 * np.pi * month / 12)),
                "month_cos": float(np.cos(2 * np.pi * month / 12)),
                **lags,
            }
            X = pd.DataFrame([row])[self.features]
            base = float(self.model.predict(X)[0])
        except (ValueError, KeyError) as e:
            self.log.warning(f"predict_price_at failed after fallback: {e}")
            return None
        mult = GRADE_MULTIPLIER.get(grade.upper(), 1.0)
        return base * mult

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
