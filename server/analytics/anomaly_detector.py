from __future__ import annotations

from sklearn.ensemble import IsolationForest

from server.analytics.feature_builder import snapshot_to_vector


class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.05,
            random_state=42,
        )
        self.is_trained = False

    def fit(self, snapshots):
        X = [snapshot_to_vector(x) for x in snapshots]

        if len(X) < 20:
            return

        self.model.fit(X)
        self.is_trained = True

    def predict(self, snapshot):
        if not self.is_trained:
            return {
                "is_anomaly": False,
                "score": 0.0,
            }

        X = [snapshot_to_vector(snapshot)]

        prediction = self.model.predict(X)[0]

        score = float(
            -self.model.score_samples(X)[0]
        )

        return {
            "is_anomaly": prediction == -1,
            "score": round(score, 4),
        }
