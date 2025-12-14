from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app.models.database import Insight
from app.models.schemas import InsightResponse, InsightHistoryItem
import logging

logger = logging.getLogger(__name__)


class InsightRepository:
    """Repository pattern for Insight database operations"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, insight_data: InsightResponse) -> Insight:
        """
        Create a new insight record in the database.

        Args:
            insight_data: InsightResponse object from the service

        Returns:
            Created Insight model
        """
        insight = Insight(
            insight_id=insight_data.insight_id,
            user_id=insight_data.user_id,
            tenant_id=insight_data.tenant_id,
            input_type=insight_data.input_summary.metric_name,  # Simplified
            input_data={
                "metric_name": insight_data.input_summary.metric_name,
                "data_points_count": insight_data.input_summary.data_points_count
            },
            features=insight_data.features.dict(),
            llm_output=insight_data.insight.dict(),
            metadata=insight_data.metadata.dict(),
            fallback_used=insight_data.metadata.fallback_used,
            processing_time_ms=insight_data.metadata.processing_time_ms,
            llm_provider=insight_data.metadata.llm_provider,
            created_at=insight_data.timestamp
        )

        self.session.add(insight)
        self.session.commit()
        self.session.refresh(insight)

        logger.info(f"Insight {insight.insight_id} saved to database")
        return insight

    def get_by_id(self, insight_id: str) -> Optional[Insight]:
        """Get insight by ID"""
        return self.session.query(Insight).filter(
            Insight.insight_id == insight_id
        ).first()

    def get_by_user(
            self,
            user_id: str,
            tenant_id: str,
            limit: int = 50,
            offset: int = 0,
            severity: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> tuple[List[Insight], int]:
        """
        Get insights for a user with filtering and pagination.

        Returns:
            Tuple of (insights list, total count)
        """
        # Base query with tenant isolation
        query = self.session.query(Insight).filter(
            Insight.user_id == user_id,
            Insight.tenant_id == tenant_id
        )

        # Apply filters
        if severity:
            query = query.filter(
                Insight.llm_output['severity'].astext == severity
            )

        if start_date:
            query = query.filter(Insight.created_at >= start_date)

        if end_date:
            query = query.filter(Insight.created_at <= end_date)

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination and ordering
        insights = query.order_by(
            desc(Insight.created_at)
        ).limit(limit).offset(offset).all()

        return insights, total_count

    def get_recent_by_tenant(self, tenant_id: str, limit: int = 100) -> List[Insight]:
        """Get recent insights for a tenant (for monitoring/analytics)"""
        return self.session.query(Insight).filter(
            Insight.tenant_id == tenant_id
        ).order_by(
            desc(Insight.created_at)
        ).limit(limit).all()
