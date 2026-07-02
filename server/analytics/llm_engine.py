import os
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class LLMAnalysisEngine:
    def __init__(self):
        """
        Initializes the unified Gemini API client using the environment variables.
        Gracefully falls back to mock data if the API key is missing.
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            try:
                # The modern SDK uses a unified Client object
                self.client = genai.Client(api_key=self.api_key)
                self.model_id = 'gemini-3.5-flash'
                logger.info("LLM Analysis Engine successfully initialized with Google GenAI SDK.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None
        else:
            logger.warning("GEMINI_API_KEY not found in environment. LLM Engine running in MOCK MODE.")
            self.client = None

    def explain_anomaly(self, metric_name: str, current_value: float, threshold: float) -> dict:
        """
        Generates a plain-English explanation and standard troubleshooting commands
        when an anomaly or threshold breach is detected by anomaly_detector.py.
        """
        if not self.client:
            return self._get_mock_anomaly_response(metric_name, current_value, threshold)

        prompt = f"""
        You are a senior DevOps and Systems Engineering assistant for a monitoring platform. 
        An automated system detected a metric anomaly:
        - Metric Monitored: {metric_name}
        - Current Value: {current_value}
        - Threshold Breached: {threshold}

        Provide a concise analysis in valid JSON format with exactly two keys:
        1. "explanation": A 2-sentence plain English explanation of what this breach means and what typically causes it.
        2. "remediation_steps": A list of 2 standard terminal commands or actions a student/admin can run to troubleshoot this.
        """
        
        try:
            # Using the new SDK's GenerateContentConfig to natively enforce JSON output
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text.strip())
        except Exception as e:
            logger.error(f"Error generating LLM anomaly analysis: {e}")
            return self._get_mock_anomaly_response(metric_name, current_value, threshold)

    def generate_health_summary(self, health_score: float, active_anomalies: list) -> str:
        """
        Generates a friendly 1-sentence status summary based on the current health score
        calculated by health_score.py to display as a banner on the UI dashboard.
        """
        if not self.client:
            status = "stable" if health_score >= 75 else "degraded"
            return f"System health is currently {status} at {health_score}%. Review active metrics below."

        anomalies_str = ", ".join(active_anomalies) if active_anomalies else "None"
        prompt = f"""
        You are an IT infrastructure assistant. Summarize the current server status for a dashboard banner.
        - Current Health Score: {health_score}/100
        - Active Anomalies: {anomalies_str}

        Write a professional, warm 1-sentence executive summary of the system's current state. 
        Keep it under 30 words.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating LLM health summary: {e}")
            return f"System health is evaluated at {health_score}%. Review active metrics for detailed insights."

    def _get_mock_anomaly_response(self, metric_name: str, current_value: float, threshold: float) -> dict:
        """Fallback mock data to ensure your demo works seamlessly even without internet or API keys."""
        return {
            "explanation": f"The system detected that {metric_name} reached {current_value}, crossing your defined safety threshold of {threshold}. This typically indicates high resource consumption or an uncontrolled process loop.",
            "remediation_steps": [
                f"Identify resource-heavy processes using: top -b -o +%CPU | head -n 10",
                "Check the service status and logs to determine if a restart is required."
            ]
        }
