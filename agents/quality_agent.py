"""Agent 1 — Quality Assessment (MobileNetV3-Large inference wrapper).

Loads the checkpoint trained in ``train_classifier.ipynb`` and classifies a
grain image into (millet, grade).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageFilter
from torchvision import models, transforms

from app.config import QUALITY_CLASSES_PATH, QUALITY_MODEL_PATH


class QualityAgent:
    def __init__(
        self,
        model_path: Optional[Path] = None,
        classes_path: Optional[Path] = None,
        device: Optional[str] = None,
    ) -> None:
        self.log = logging.getLogger("QualityAgent")
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        cp = Path(classes_path or QUALITY_CLASSES_PATH)
        if cp.exists():
            with open(cp) as f:
                self.classes: list[str] = json.load(f)
        else:
            self.log.warning(f"{cp} missing — using default class list")
            self.classes = [
                "Bajra grade a", "Bajra grade b",
                "jowar grade a", "Jowar grade b", "jowar grade c",
                "Ragi grade A", "Ragi grade b",
            ]

        self.model = models.mobilenet_v3_large(weights=None)
        self.model.classifier[3] = nn.Linear(
            self.model.classifier[3].in_features, len(self.classes)
        )
        mp = Path(model_path or QUALITY_MODEL_PATH)
        if mp.exists():
            self.model.load_state_dict(torch.load(mp, map_location=self.device))
            self.log.info(f"Loaded checkpoint {mp}")
        else:
            self.log.warning(f"No checkpoint at {mp} — random weights (demo mode)")
        self.model.eval().to(self.device)

        self.tf = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    _MILLET_TOKENS = {"jowar", "bajra", "ragi"}
    BLUR_THRESHOLD = 500.0  # below this = too blurry

    @staticmethod
    def _is_blurry(pil_img: Image.Image) -> tuple[bool, float]:
        """Check if image is too blurry using Laplacian variance."""
        grey = pil_img.convert("L").resize((224, 224))
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
        """Extract (millet, grade) from labels like 'augmented jowar grade a'.

        Scans tokens for a known millet name (jowar/bajra/ragi) and takes the
        final token as the grade letter. Robust to prefixes like 'augmented'.
        """
        tokens = name.strip().lower().split()
        millet = next((t for t in tokens if t in cls._MILLET_TOKENS), tokens[0])
        grade = tokens[-1].upper()
        return millet, grade

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

        # Reject blurry images
        blurry, blur_score = self._is_blurry(pil_img)
        if blurry:
            self.log.warning(f"Image too blurry (score={blur_score:.1f})")
            return {
                "millet": "unknown",
                "grade": "INVALID",
                "quality_score": 0.0,
                "confidence": 0.0,
                "top3": [],
                "quality_source": "model",
                "invalid_image": True,
                "error": "Image is too blurry. Please upload a clear, focused photo of the grains.",
            }

        img = self.tf(pil_img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            probs = torch.softmax(self.model(img), 1)[0].cpu().numpy()
        idx = int(probs.argmax())
        conf = float(probs[idx])
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
