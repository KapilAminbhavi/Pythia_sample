from app.services.anomaly_detector import AnomalyResult
from typing import Optional, Dict, Any
from app.models.schemas import FeatureSet

class PromptBuilder:
    @staticmethod
    def build_insight_prompt(
            metric_name: str,
            features: FeatureSet,
            input_data: Dict[str, Any],
            anomaly_result: Optional[AnomalyResult] = None  # NEW
    ) -> str:
        """Build LLM prompt with anomaly detection context"""

        # Base prompt
        prompt = f"""You are analyzing business metrics for an enterprise data platform.

METRIC: {metric_name}
CURRENT VALUE: {features.current_value}
PREVIOUS VALUE: {features.previous_value}
CHANGE: {features.change_absolute} ({features.change_percent:+.2f}%)
RULE-BASED SEVERITY: {features.severity}
"""

        # Add anomaly detection context if available
        if anomaly_result:
            prompt += f"""
STATISTICAL ANOMALY ANALYSIS:
- Method: {anomaly_result.method}
- Is Anomaly: {anomaly_result.is_anomaly}
- Z-Score: {anomaly_result.z_score:.2f}
- Details: {anomaly_result.details.get('interpretation', 'N/A')}
"""

        prompt += """
TASK:
Generate a concise business insight explaining this change. Your response must be actionable and relevant to C-level stakeholders.

REQUIREMENTS:
1. Summary: 2-3 sentences explaining what happened and why it matters
2. Severity: critical | high | medium | low (you may adjust from rule-based if you have good reason)
3. Confidence: 0.0-1.0 based on data quality and pattern clarity
4. Recommended Actions: 2-4 specific, actionable steps
5. Key Findings: 2-4 bullet points highlighting important patterns

OUTPUT FORMAT: Return ONLY valid JSON matching this schema:
{
  "summary": "string",
  "severity": "critical|high|medium|low",
  "confidence": 0.85,
  "recommended_actions": ["action1", "action2"],
  "key_findings": ["finding1", "finding2"]
}

Generate your response now."""

        return prompt

    @staticmethod
    def get_response_schema() -> Dict[str, Any]:
        """
        Returns the JSON schema for the expected LLM response.
        This ensures structured output from the LLM.
        """
        return {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of the insight (2-3 sentences)"
                },
                "severity": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Severity level of the insight"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence score between 0 and 1"
                },
                "recommended_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 2-4 specific actionable steps",
                    "minItems": 2,
                    "maxItems": 4
                },
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 2-4 key findings",
                    "minItems": 2,
                    "maxItems": 4
                }
            },
            "required": ["summary", "severity", "confidence", "recommended_actions", "key_findings"]
        }