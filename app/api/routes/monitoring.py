from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.drift_monitor import DriftMonitor
from typing import Dict

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/drift")
async def check_drift(
        days: int = Query(7, ge=1, le=90),
        threshold: float = Query(0.3, ge=0.0, le=1.0),
        db: Session = Depends(get_db)
) -> Dict:
    """
    Check for model drift.

    Compares LLM outputs to rule-based baselines.
    """
    monitor = DriftMonitor(db)
    return monitor.detect_drift(days=days, disagreement_threshold=threshold)


@router.get("/output-distribution")
async def get_output_distribution(
        days: int = Query(30, ge=1, le=365),
        db: Session = Depends(get_db)
) -> Dict:
    """
    Analyze LLM output distribution over time.

    Tracks summary length and confidence trends.
    """
    monitor = DriftMonitor(db)
    return monitor.get_output_distribution(days=days)


@router.get("/compare-prompts")
async def compare_prompt_versions(
        version_a: str = Query(..., description="First prompt version"),
        version_b: str = Query(..., description="Second prompt version"),
        days: int = Query(7, ge=1, le=90),
        db: Session = Depends(get_db)
) -> Dict:
    """
    Compare two prompt versions (A/B testing).

    Requires prompt_version to be stored in metadata.
    """
    monitor = DriftMonitor(db)
    return monitor.compare_prompt_versions(version_a, version_b, days=days)