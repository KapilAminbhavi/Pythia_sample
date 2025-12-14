from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID, uuid4


# ===== Request Schemas =====

class MetricsData(BaseModel):
    metric_name: str
    values: List[float] = Field(..., min_items=2)
    timestamps: Optional[List[datetime]] = None


class TextData(BaseModel):
    content: str = Field(..., min_length=1)


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    value: float


class TimeSeriesData(BaseModel):
    series_name: str
    data_points: List[TimeSeriesPoint] = Field(..., min_items=2)


class ContextConfig(BaseModel):
    baseline: Optional[float] = None
    thresholds: Optional[Dict[str, float]] = None


class InsightRequest(BaseModel):
    user_id: str
    tenant_id: str
    input_type: Literal["metrics", "text", "timeseries"]
    data: Dict[str, Any]  # Will be validated based on input_type
    context: Optional[ContextConfig] = None

    @validator('data')
    def validate_data_format(cls, v, values):
        input_type = values.get('input_type')
        try:
            if input_type == 'metrics':
                return MetricsData(**v).dict()
            elif input_type == 'text':
                return TextData(**v).dict()
            elif input_type == 'timeseries':
                return TimeSeriesData(**v).dict()
        except Exception as e:
            raise ValueError(f"Invalid data format for {input_type}: {str(e)}")
        return v


# ===== Response Schemas =====

class FeatureSet(BaseModel):
    previous_value: float
    current_value: float
    change_absolute: float
    change_percent: float
    severity: Literal["critical", "high", "medium", "low"]


class InsightOutput(BaseModel):
    summary: str
    severity: Literal["critical", "high", "medium", "low"]
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_actions: List[str]
    key_findings: List[str]


class InputSummary(BaseModel):
    metric_name: str
    data_points_count: int
    time_range: Optional[Dict[str, datetime]] = None


class ResponseMetadata(BaseModel):
    processing_time_ms: int
    llm_provider: str
    model_version: str
    fallback_used: bool


class InsightResponse(BaseModel):
    insight_id: UUID = Field(default_factory=uuid4)
    user_id: str
    tenant_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    input_summary: InputSummary
    features: FeatureSet
    insight: InsightOutput
    metadata: ResponseMetadata


# ===== History Schemas =====

class InsightHistoryItem(BaseModel):
    insight_id: UUID
    timestamp: datetime
    metric_name: str
    severity: str
    summary: str
    change_percent: float


class InsightHistoryResponse(BaseModel):
    user_id: str
    tenant_id: str
    total_count: int
    returned_count: int
    insights: List[InsightHistoryItem]
    pagination: Dict[str, Any]
