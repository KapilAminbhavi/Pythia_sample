import json
import asyncio
import random
from typing import Dict, Any
from .llm_base import LLMClient


class MockLLMClient(LLMClient):
    """Mock LLM for testing without API costs"""

    def __init__(self):
        self.model = "mock-llm-v1"

    async def generate(
            self,
            prompt: str,
            response_schema: Dict[str, Any],
            temperature: float = 0.7,
            max_tokens: int = 1000
    ) -> str:
        """Generate mock insights based on prompt patterns"""

        # Simulate API latency
        await asyncio.sleep(random.uniform(0.5, 2.0))

        # Parse severity from prompt (crude extraction)
        severity = "medium"
        if "critical" in prompt.lower() or "spike" in prompt.lower():
            severity = "high"
        if "severe" in prompt.lower():
            severity = "critical"

        # Generate mock response
        mock_response = {
            "summary": f"Analysis indicates a notable trend change. The data shows significant movement that warrants attention from stakeholders.",
            "severity": severity,
            "confidence": round(random.uniform(0.75, 0.95), 2),
            "recommended_actions": [
                "Review recent operational changes that may have influenced this metric",
                "Monitor closely over the next 24-48 hours for trend confirmation",
                "Alert relevant team members to investigate root causes"
            ],
            "key_findings": [
                "Metric deviation exceeds typical variance thresholds",
                "Pattern suggests potential systematic change rather than noise",
                "Timing correlates with recent business events"
            ]
        }

        return json.dumps(mock_response)

    def get_model_name(self) -> str:
        return self.model