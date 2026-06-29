from __future__ import annotations


def generate_incident(snapshot, anomaly_result):
    if not anomaly_result["is_anomaly"]:
        return None

    severity = "LOW"

    if anomaly_result["score"] > 0.8:
        severity = "HIGH"
    elif anomaly_result["score"] > 0.5:
        severity = "MEDIUM"

    return {
        "incident_type": "RESOURCE_ANOMALY",
        "severity": severity,
        "confidence": anomaly_result["score"],
        "description": (
            f"Potential anomaly detected. "
            f"CPU={snapshot.get('cpu_usage')} "
            f"RAM={snapshot.get('ram_usage')} "
            f"Disk={snapshot.get('disk_usage')}"
        ),
    }
