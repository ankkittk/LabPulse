"""
forecasting.py

Predictive analytics module for LabPulse AI.

Responsibilities
----------------
1. Train lightweight forecasting models.
2. Predict future CPU/RAM/Disk usage.
3. Predict future health score.
4. Estimate overall machine risk.

This module intentionally contains:
- NO database logic
- NO FastAPI
- NO dashboard code
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
from sklearn.linear_model import LinearRegression

from server.analytics.health_score import assess_health


# ==========================================================
# Prediction Result
# ==========================================================

@dataclass(frozen=True)
class PredictionResult:
    cpu_prediction: float
    ram_prediction: float
    disk_prediction: float
    predicted_health: float
    risk_level: str


# ==========================================================
# Resource Forecaster
# ==========================================================

class ResourceForecaster:
    """
    Lightweight resource forecasting engine.

    Uses Linear Regression to forecast the next
    CPU, RAM and Disk usage based on historical
    snapshots.
    """

    MIN_HISTORY = 5

    def __init__(self):

        self.cpu_model = LinearRegression()
        self.ram_model = LinearRegression()
        self.disk_model = LinearRegression()

        self.is_trained = False

        self.history_size = 0

    # ------------------------------------------------------

    @staticmethod
    def _clamp(value: float) -> float:
        """
        Restrict predictions to valid percentage range.
        """
        return max(0.0, min(100.0, value))

    # ------------------------------------------------------

    def reset(self) -> None:
        """
        Reset all trained models.
        """

        self.__init__()

    # ------------------------------------------------------

    def train(
        self,
        snapshots: List[dict],
    ) -> None:
        """
        Train forecasting models using historical
        telemetry snapshots.
        """

        if len(snapshots) < self.MIN_HISTORY:
            return

        self.history_size = len(snapshots)

        x = np.arange(self.history_size).reshape(-1, 1)

        cpu = np.array(
            [
                s.get("cpu_usage", 0.0)
                for s in snapshots
            ]
        )

        ram = np.array(
            [
                s.get("ram_usage", 0.0)
                for s in snapshots
            ]
        )

        disk = np.array(
            [
                s.get("disk_usage", 0.0)
                for s in snapshots
            ]
        )

        self.cpu_model.fit(x, cpu)
        self.ram_model.fit(x, ram)
        self.disk_model.fit(x, disk)

        self.is_trained = True

    # ------------------------------------------------------

    def predict(
        self,
        steps_ahead: int = 1,
    ) -> PredictionResult:
        """
        Predict resource usage a given number
        of snapshots into the future.

        steps_ahead=1 means:
        Predict the very next snapshot.
        """

        if not self.is_trained:

            return PredictionResult(
                cpu_prediction=0.0,
                ram_prediction=0.0,
                disk_prediction=0.0,
                predicted_health=0.0,
                risk_level="UNKNOWN",
            )

        next_index = np.array(
            [[self.history_size + steps_ahead - 1]]
        )

        cpu = self._clamp(
            float(
                self.cpu_model.predict(next_index)[0]
            )
        )

        ram = self._clamp(
            float(
                self.ram_model.predict(next_index)[0]
            )
        )

        disk = self._clamp(
            float(
                self.disk_model.predict(next_index)[0]
            )
        )

        health = assess_health(
            cpu,
            ram,
            disk,
        )

        return PredictionResult(
            cpu_prediction=round(cpu, 2),
            ram_prediction=round(ram, 2),
            disk_prediction=round(disk, 2),
            predicted_health=round(
                health.score,
                2,
            ),
            risk_level=self._risk_level(
                health.score
            ),
        )

    # ------------------------------------------------------

    def forecast(
        self,
        snapshots: List[dict],
        steps_ahead: int = 1,
    ) -> PredictionResult:
        """
        Convenience method.

        Train the models and immediately
        return a prediction.
        """

        self.train(snapshots)

        return self.predict(
            steps_ahead=steps_ahead
        )

    # ------------------------------------------------------

    @staticmethod
    def _risk_level(
        predicted_health: float,
    ) -> str:
        """
        Convert predicted health score
        into a qualitative risk level.
        """

        if predicted_health >= 80:
            return "LOW"

        if predicted_health >= 60:
            return "MEDIUM"

        if predicted_health >= 40:
            return "HIGH"

        return "CRITICAL"
