"""
detector.py — Fraud Detection using IsolationForest
होटल लिस्टिंग में धोखाधड़ी का पता लगाता है।
Detects potentially fraudulent hotel listings using IsolationForest + rule-based checks.
"""

from __future__ import annotations

import os
import csv
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# ज्ञात scam keywords / Known scam patterns in hotel names
_DEFAULT_SCAM_KEYWORDS = [
    "fake palace",
    "free stay",
    "100% discount",
    "guaranteed visa",
]

# Risk thresholds / जोखिम सीमाएँ
RISK_LOW = 0.3
RISK_HIGH = 0.6

# Suspicious price / rating thresholds
SUSPICIOUS_PRICE_MIN = 150      # ₹ below this is suspicious
SUSPICIOUS_RATING_MAX = 4.9     # perfect rating is suspicious


@dataclass
class FraudDetector:
    """
    Isolation Forest + rule-based fraud detector for hotel listings.
    होटल लिस्टिंग की धोखाधड़ी जाँचता है।
    """

    scam_keywords: list[str] = field(default_factory=lambda: list(_DEFAULT_SCAM_KEYWORDS))
    _model: IsolationForest = field(init=False, repr=False, default=None)
    _is_fitted: bool = field(init=False, default=False)

    def fit_price_model(self, hotels_df: pd.DataFrame) -> None:
        """
        होटल price data पर IsolationForest train करता है।
        Trains an IsolationForest on hotel price_per_night values.
        """
        if hotels_df.empty or "price_per_night" not in hotels_df.columns:
            return

        prices = hotels_df["price_per_night"].dropna().values.reshape(-1, 1)
        if len(prices) < 2:
            return

        self._model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
        )
        self._model.fit(prices)
        self._is_fitted = True

    def score_listing(self, listing: dict) -> float:
        """
        एक होटल listing का fraud risk score (0.0–1.0) देता है।
        Returns a fraud risk score between 0.0 (safe) and 1.0 (high risk).
        """
        scores: list[float] = []

        # Rule 1: Known scam keywords in name
        name = str(listing.get("name", "")).lower()
        if any(kw in name for kw in self.scam_keywords):
            scores.append(1.0)

        # Rule 2: Price anomaly via IsolationForest
        price = listing.get("price_per_night", None)
        if price is not None and self._is_fitted:
            arr = np.array([[float(price)]])
            # IsolationForest: -1 = anomaly, +1 = normal → map to 0/1
            pred = self._model.predict(arr)[0]
            scores.append(0.8 if pred == -1 else 0.0)

        # Rule 3: Suspiciously high rating (> 4.9)
        try:
            rating = float(listing.get("rating", 0) or 0)
            if rating >= SUSPICIOUS_RATING_MAX:
                scores.append(0.5)
        except (ValueError, TypeError):
            pass

        # Rule 4: Suspiciously low price (< ₹150)
        try:
            if float(price or 0) < SUSPICIOUS_PRICE_MIN:
                scores.append(0.6)
        except (ValueError, TypeError):
            pass

        if not scores:
            return 0.0
        return float(np.clip(np.mean(scores), 0.0, 1.0))

    def risk_label(self, score: float) -> str:
        """
        Risk score को emoji label में बदलता है।
        Converts a risk score to a human-readable risk label with emoji.
        """
        if score < RISK_LOW:
            return f"🟢 LOW ({score:.2f})"
        if score < RISK_HIGH:
            return f"🟡 MODERATE ({score:.2f})"
        return f"🔴 HIGH ({score:.2f})"

    def load_known_scams(self, scam_file: str) -> None:
        """
        CSV फ़ाइल से ज्ञात scam keywords लोड करता है।
        Loads known scam keywords from a CSV file (column: 'keyword').
        """
        if not os.path.exists(scam_file):
            print(f"[WARN] Scam file not found: {scam_file}")
            return

        with open(scam_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kw = row.get("keyword", "").strip().lower()
                if kw and kw not in self.scam_keywords:
                    self.scam_keywords.append(kw)
        print(f"[INFO] Loaded {len(self.scam_keywords)} scam keywords from {scam_file}")

    def check_listing(self, listing: dict) -> dict:
        """
        Listing का complete fraud check करता है।
        Returns a dict with risk_score and risk_label for a listing.
        """
        score = self.score_listing(listing)
        return {
            "name": listing.get("name", "Unknown"),
            "price_per_night": listing.get("price_per_night", ""),
            "rating": listing.get("rating", ""),
            "risk_score": score,
            "risk_label": self.risk_label(score),
        }
