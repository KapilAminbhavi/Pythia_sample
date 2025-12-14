from typing import List, Dict, Any
from app.models.schemas import FeatureSet
from app.config import Settings


class FeatureExtractor:
    def __init__(self, settings: Settings):
        self.settings = settings

    def extract_from_metrics(self, values: List[float], context: Dict[str, Any] = None) -> FeatureSet:
        """
        Extract features from time-series metrics.
        Implements simple but robust change detection.
        """
        if len(values) < 2:
            raise ValueError("Need at least 2 values for comparison")

        previous_value = values[-2]
        current_value = values[-1]
        change_absolute = current_value - previous_value

        # Handle division by zero gracefully
        if previous_value == 0:
            if current_value == 0:
                change_percent = 0.0
            else:
                # Treat as infinite increase, cap at 1000%
                change_percent = 1000.0 if current_value > 0 else -1000.0
        else:
            change_percent = (change_absolute / previous_value) * 100

        # Determine severity using configurable thresholds
        thresholds = context.get('thresholds') if context else None
        if thresholds is None:
            thresholds = {
                'critical': self.settings.severity_threshold_critical,
                'high': self.settings.severity_threshold_high,
                'medium': self.settings.severity_threshold_medium
            }

        abs_change = abs(change_percent)
        if abs_change >= thresholds.get('critical', 50):
            severity = "critical"
        elif abs_change >= thresholds.get('high', 25):
            severity = "high"
        elif abs_change >= thresholds.get('medium', 10):
            severity = "medium"
        else:
            severity = "low"

        return FeatureSet(
            previous_value=previous_value,
            current_value=current_value,
            change_absolute=round(change_absolute, 2),
            change_percent=round(change_percent, 2),
            severity=severity
        )

    def extract_from_text(self, text: str) -> FeatureSet:
        """
        Placeholder for text-based feature extraction.
        In production, this would use NLP techniques.
        """
        # Simple heuristic: text length and keyword presence
        word_count = len(text.split())

        # Mock severity based on urgency keywords
        urgency_keywords = ['urgent', 'critical', 'emergency', 'immediate']
        severity = "high" if any(kw in text.lower() for kw in urgency_keywords) else "medium"

        return FeatureSet(
            previous_value=0.0,
            current_value=float(word_count),
            change_absolute=float(word_count),
            change_percent=0.0,
            severity=severity
        )
