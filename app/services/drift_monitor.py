from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.database import Insight
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DriftMonitor:
    """
    Monitor model drift by comparing LLM outputs to rule-based baselines.
    """

    def __init__(self, session: Session):
        self.session = session

    def detect_drift(
            self,
            days: int = 7,
            disagreement_threshold: float = 0.3
    ) -> Dict:
        """
        Detect drift by comparing LLM severity vs rule-based severity.

        Args:
            days: Look back this many days
            disagreement_threshold: Alert if disagreement rate exceeds this

        Returns:
            Dictionary with drift metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get recent insights
        insights = self.session.query(Insight).filter(
            Insight.created_at >= cutoff_date
        ).all()

        if not insights:
            return {
                "status": "no_data",
                "message": "Not enough data to detect drift"
            }

        total = len(insights)
        disagreements = 0
        severity_mismatches = []
        confidence_drop = []

        for insight in insights:
            rule_severity = insight.features.get('severity', 'unknown')
            llm_severity = insight.llm_output.get('severity', 'unknown')
            llm_confidence = insight.llm_output.get('confidence', 0.0)

            # Track disagreements
            if rule_severity != llm_severity:
                disagreements += 1
                severity_mismatches.append({
                    "insight_id": str(insight.insight_id),
                    "rule_severity": rule_severity,
                    "llm_severity": llm_severity,
                    "created_at": insight.created_at.isoformat()
                })

            # Track low confidence
            if llm_confidence < 0.5:
                confidence_drop.append({
                    "insight_id": str(insight.insight_id),
                    "confidence": llm_confidence
                })

        drift_rate = disagreements / total if total > 0 else 0

        # Check for drift
        is_drifting = drift_rate > disagreement_threshold

        result = {
            "status": "drift_detected" if is_drifting else "normal",
            "drift_rate": round(drift_rate, 3),
            "total_insights": total,
            "disagreements": disagreements,
            "threshold": disagreement_threshold,
            "period_days": days,
            "low_confidence_count": len(confidence_drop),
            "severity_mismatches": severity_mismatches[:10],  # Top 10
            "recommendation": self._get_recommendation(drift_rate, disagreement_threshold)
        }

        if is_drifting:
            logger.warning(f"Model drift detected: {drift_rate:.1%} disagreement rate")

        return result

    def _get_recommendation(self, drift_rate: float, threshold: float) -> str:
        """Generate recommendation based on drift rate"""
        if drift_rate < threshold * 0.5:
            return "No action needed. LLM and rules are aligned."
        elif drift_rate < threshold:
            return "Monitor closely. Slight divergence detected."
        elif drift_rate < threshold * 1.5:
            return "Review prompt templates. Significant drift detected."
        else:
            return "URGENT: Major drift detected. Review LLM provider updates and consider prompt retraining."

    def get_output_distribution(self, days: int = 30) -> Dict:
        """
        Analyze distribution of LLM outputs over time.
        Useful for detecting quality degradation.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Query aggregated metrics
        results = self.session.query(
            func.date(Insight.created_at).label('date'),
            func.avg(func.length(Insight.llm_output['summary'].astext)).label('avg_summary_length'),
            func.avg((Insight.llm_output['confidence'].astext.cast(float))).label('avg_confidence'),
            func.count().label('count')
        ).filter(
            Insight.created_at >= cutoff_date
        ).group_by(
            func.date(Insight.created_at)
        ).order_by(
            desc('date')
        ).all()

        return {
            "period_days": days,
            "daily_metrics": [
                {
                    "date": str(r.date),
                    "avg_summary_length": round(r.avg_summary_length, 1) if r.avg_summary_length else 0,
                    "avg_confidence": round(r.avg_confidence, 2) if r.avg_confidence else 0,
                    "insight_count": r.count
                }
                for r in results
            ]
        }

    def compare_prompt_versions(
            self,
            version_a: str,
            version_b: str,
            days: int = 7
    ) -> Dict:
        """
        Compare performance of two prompt versions (A/B testing).

        Requires storing prompt_version in metadata.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get insights for each version
        version_a_insights = self.session.query(Insight).filter(
            Insight.created_at >= cutoff_date,
            Insight.metadata['prompt_version'].astext == version_a
        ).all()

        version_b_insights = self.session.query(Insight).filter(
            Insight.created_at >= cutoff_date,
            Insight.metadata['prompt_version'].astext == version_b
        ).all()

        def analyze_version(insights: List[Insight]) -> Dict:
            if not insights:
                return {"count": 0}

            confidences = [i.llm_output.get('confidence', 0) for i in insights]
            processing_times = [i.processing_time_ms for i in insights]
            fallback_count = sum(1 for i in insights if i.fallback_used)

            return {
                "count": len(insights),
                "avg_confidence": round(sum(confidences) / len(confidences), 3),
                "avg_processing_time_ms": round(sum(processing_times) / len(processing_times), 1),
                "fallback_rate": round(fallback_count / len(insights), 3),
                "success_rate": round(1 - (fallback_count / len(insights)), 3)
            }

        return {
            "version_a": version_a,
            "version_a_metrics": analyze_version(version_a_insights),
            "version_b": version_b,
            "version_b_metrics": analyze_version(version_b_insights),
            "period_days": days,
            "recommendation": self._compare_versions(
                analyze_version(version_a_insights),
                analyze_version(version_b_insights)
            )
        }

    def _compare_versions(self, metrics_a: Dict, metrics_b: Dict) -> str:
        """Generate recommendation from A/B test"""
        if metrics_a.get("count", 0) < 100 or metrics_b.get("count", 0) < 100:
            return "Need more data (min 100 samples each)"

        conf_a = metrics_a.get("avg_confidence", 0)
        conf_b = metrics_b.get("avg_confidence", 0)

        if conf_b > conf_a * 1.1:
            return f"Version B is significantly better (+{((conf_b / conf_a - 1) * 100):.1f}% confidence)"
        elif conf_a > conf_b * 1.1:
            return "Version A is better. Keep current version."
        else:
            return "No significant difference. Choose based on other factors."