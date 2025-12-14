from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from app.models.schemas import InsightRequest, InsightResponse, InsightHistoryResponse
from app.services.insight_service import InsightService
from app.repositories.insight_repository import InsightRepository
from app.api.dependencies import get_insight_service
from app.database.connection import get_db
from app.utils.rate_limiter import limiter
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["insights"])


@router.post("/generate-insight", response_model=InsightResponse)
@limiter.limit("10/minute")  # Rate limit per IP
async def generate_insight(
        request: Request,  # Required for rate limiter
        insight_request: InsightRequest,
        service: InsightService = Depends(get_insight_service),
        db: Session = Depends(get_db)
):
    """
    Generate AI-powered insights from input data.
    Rate limited to 10 requests per minute per IP.
    """
    try:
        logger.info(f"Insight request from user={insight_request.user_id}, "
                    f"tenant={insight_request.tenant_id}")

        # Generate insight
        result = await service.generate_insight(insight_request)

        # Save to database
        repo = InsightRepository(db)
        repo.create(result)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/insight-history/{user_id}", response_model=InsightHistoryResponse)
@limiter.limit("30/minute")
async def get_insight_history(
        request: Request,
        user_id: str,
        tenant_id: str = Query(..., description="Tenant ID for data isolation"),
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        severity: Optional[str] = Query(None, regex="^(critical|high|medium|low)$"),
        db: Session = Depends(get_db)
):
    """
    Retrieve insight history for a user.
    Rate limited to 30 requests per minute per IP.
    """
    try:
        repo = InsightRepository(db)
        insights, total_count = repo.get_by_user(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            severity=severity
        )

        # Convert to response format
        from app.models.schemas import InsightHistoryItem
        history_items = []
        for insight in insights:
            history_items.append(InsightHistoryItem(
                insight_id=insight.insight_id,
                timestamp=insight.created_at,
                metric_name=insight.input_data.get('metric_name', 'Unknown'),
                severity=insight.llm_output.get('severity', 'low'),
                summary=insight.llm_output.get('summary', '')[:200],  # Truncate
                change_percent=insight.features.get('change_percent', 0.0)
            ))

        return InsightHistoryResponse(
            user_id=user_id,
            tenant_id=tenant_id,
            total_count=total_count,
            returned_count=len(history_items),
            insights=history_items,
            pagination={
                "limit": limit,
                "offset": offset,
                "has_more": total_count > (offset + len(history_items))
            }
        )

    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")