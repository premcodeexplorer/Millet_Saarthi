"""Agent 1 — Quality Assessment (EfficientNetB0 inference wrapper).

Loads the retrained Keras checkpoint (``best_model.h5``) and classifies a grain
image into (millet, grade). Predictions below 75% confidence are rejected as
"Not a valid grain image" so the planner aborts the pipeline.

EfficientNetB0 expects raw 0-255 pixels — its own ``preprocess_input`` applies
the right scaling internally, so we MUST NOT divide by 255 ourselves.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

# Silence TF info logs before import
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import keras
import numpy as np
from keras.applications.efficientnet import preprocess_input
from PIL import Image, ImageFilter

from app.config import (
    IMG_SIZE,
    QUALITY_CLASSES_PATH,
    QUALITY_CONFIDENCE_THRESHOLD,
    QUALITY_MODEL_PATH,
)


class QualityAgent:
    BLUR_THRESHOLD = 500.0
    _MILLET_TOKENS = {"jowar", "bajra", "ragi"}

    def __init__(
        self,
        model_path: Optional[Path] = None,
        classes_path: Optional[Path] = None,
    ) -> None:
        self.log = logging.getLogger("QualityAgent")

        cp = Path(classes_path or QUALITY_CLASSES_PATH)
        if cp.exists():
            with open(cp) as f:
                self.classes: list[str] = json.load(f)
        else:
            self.log.warning(f"{cp} missing — using default class list")
            self.classes = [
                "Bajra Grade A", "Bajra Grade B",
                "Jowar Grade A", "Jowar Grade B", "Jowar Grade C",
                "Ragi Grade A", "Ragi Grade B",
            ]

        mp = Path(model_path or QUALITY_MODEL_PATH)
        if mp.exists():
            self.model = keras.models.load_model(mp, compile=False)
            self.log.info(f"Loaded EfficientNetB0 checkpoint {mp}")
        else:
            self.log.warning(f"No checkpoint at {mp} — demo mode (mock predictions)")
            self.model = None

    @staticmethod
    def _is_blurry(pil_img: Image.Image) -> tuple[bool, float]:
        grey = pil_img.convert("L").resize((IMG_SIZE, IMG_SIZE))
        edges = grey.filter(ImageFilter.Kernel(
            size=(3, 3),
            kernel=[-1, -1, -1, -1, 8, -1, -1, -1, -1],
            scale=1, offset=0,
        ))
        arr = np.array(edges, dtype=np.float64)
        variance = float(arr.var())
        return variance < QualityAgent.BLUR_THRESHOLD, variance

    @classmethod
    def _parse_class(cls, name: str) -> tuple[str, str]:
        tokens = name.strip().lower().split()
        millet = next((t for t in tokens if t in cls._MILLET_TOKENS), tokens[0])
        grade = tokens[-1].upper()
        return millet, grade

    def _predict_class(self, pil_img: Image.Image) -> tuple[int, np.ndarray]:
        """Run the EfficientNetB0 forward pass. Returns (top_idx, probs)."""
        # Resize to 224x224, keep raw 0-255 pixels — preprocess_input scales internally
        arr = np.array(pil_img.resize((IMG_SIZE, IMG_SIZE)), dtype=np.float32)
        arr = preprocess_input(arr)
        arr = np.expand_dims(arr, 0)
        logits = self.model.predict(arr, verbose=0)[0]
        s = float(logits.sum())
        probs = logits if 0.99 <= s <= 1.01 else self._softmax(logits)
        return int(probs.argmax()), probs

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        e = np.exp(x - x.max())
        return e / e.sum()

    def predict(self, state: dict) -> dict:
        if "image_path" not in state:
            raise ValueError("QualityAgent requires 'image_path' in state")
        path = Path(state["image_path"])
        if not path.exists():
            self.log.warning(f"Image not found ({path}) — mock output")
            return {
                "millet": "jowar", "grade": "A",
                "quality_score": 0.87, "confidence": 0.92,
                "quality_source": "mock",
            }
        pil_img = Image.open(path).convert("RGB")

        blurry, blur_score = self._is_blurry(pil_img)
        if blurry:
            self.log.warning(f"Image too blurry (score={blur_score:.1f})")
            return {
                "millet": "unknown", "grade": "INVALID",
                "quality_score": 0.0, "confidence": 0.0,
                "top3": [], "quality_source": "model",
                "invalid_image": True,
                "error": "Image is too blurry. Please upload a clear, focused photo of the grains.",
            }

        if self.model is None:
            return {
                "millet": "jowar", "grade": "A",
                "quality_score": 0.87, "confidence": 0.92,
                "quality_source": "mock",
            }

        idx, probs = self._predict_class(pil_img)
        conf = float(probs[idx])

        # Reject if confidence below threshold — orchestrator/planner will abort
        if conf < QUALITY_CONFIDENCE_THRESHOLD:
            self.log.warning(
                f"Confidence {conf:.2f} < {QUALITY_CONFIDENCE_THRESHOLD} — rejecting"
            )
            return {
                "millet": "unknown", "grade": "INVALID",
                "quality_score": round(conf, 3), "confidence": round(conf, 3),
                "top3": [], "quality_source": "model",
                "invalid_image": True,
                "error": "Not a valid grain image",
            }

        millet, grade = self._parse_class(self.classes[idx])
        top3_idx = probs.argsort()[-3:][::-1]
        top3 = [
            {"class": self.classes[int(i)], "prob": round(float(probs[int(i)]), 3)}
            for i in top3_idx
        ]

        return {
            "millet": millet,
            "grade": grade,
            "quality_score": round(conf, 3),
            "confidence": round(conf, 3),
            "top3": top3,
            "quality_source": "model",
        }
