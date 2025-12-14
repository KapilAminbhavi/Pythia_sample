from sqlalchemy import Column, String, Float, Boolean, DateTime, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Insight(Base):
    """
    SQLAlchemy model for storing generated insights.
    Uses JSONB for flexible schema and efficient querying.
    """
    __tablename__ = "insights"

    # Primary key
    insight_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    # User identification
    user_id = Column(String(255), nullable=False)
    tenant_id = Column(String(255), nullable=False)

    # Input data (flexible JSONB)
    input_type = Column(String(50), nullable=False)  # 'metrics', 'text', 'timeseries'
    input_data = Column(JSONB, nullable=False)

    # Extracted features (JSONB for flexibility)
    features = Column(JSONB, nullable=False)

    # LLM generated output
    llm_output = Column(JSONB, nullable=False)

    # Metadata - CHANGED FROM 'metadata' to 'insight_metadata'
    insight_metadata = Column(JSONB, nullable=False, default={})
    fallback_used = Column(Boolean, default=False)

    # Processing info
    processing_time_ms = Column(Float)
    llm_provider = Column(String(50))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_tenant_created', 'user_id', 'tenant_id', 'created_at'),
        Index('idx_tenant_severity', 'tenant_id', text("(llm_output->>'severity')"), 'created_at'),
        Index('idx_created_at', 'created_at'),
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "insight_id": str(self.insight_id),
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "input_type": self.input_type,
            "input_data": self.input_data,
            "features": self.features,
            "llm_output": self.llm_output,
            "metadata": self.insight_metadata,  # Keep the dict key as 'metadata' for API compatibility
            "fallback_used": self.fallback_used,
            "created_at": self.created_at.isoformat()
        }