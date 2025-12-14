from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List
from app.models.schemas import InsightRequest
from app.tasks.insight_tasks import generate_insight_async, batch_generate_insights
from celery.result import AsyncResult
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/async", tags=["async-insights"])


class AsyncInsightResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE
    result: dict = None
    error: str = None


@router.post("/generate-insight", response_model=AsyncInsightResponse)
async def generate_insight_async_endpoint(
        request: InsightRequest,
        background_tasks: BackgroundTasks
):
    """
    Submit insight generation as an async task.
    Returns immediately with a task_id.

    Use GET /async/task-status/{task_id} to check progress.
    """
    try:
        # Submit to Celery
        task = generate_insight_async.delay(request.dict())

        logger.info(f"Async task submitted: {task.id}")

        return AsyncInsightResponse(
            task_id=task.id,
            status="submitted",
            message="Insight generation started. Check status with task_id."
        )

    except Exception as e:
        logger.error(f"Failed to submit async task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Check the status of an async insight generation task.

    Status values:
    - PENDING: Task is waiting to be executed
    - STARTED: Task has been started
    - SUCCESS: Task completed successfully
    - FAILURE: Task failed
    """
    try:
        task_result = AsyncResult(task_id)

        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.state
        )

        if task_result.state == 'SUCCESS':
            response.result = task_result.result
        elif task_result.state == 'FAILURE':
            response.error = str(task_result.info)

        return response

    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-generate", response_model=AsyncInsightResponse)
async def batch_generate_insights_endpoint(requests: List[InsightRequest]):
    """
    Submit multiple insights for batch processing.
    Useful for bulk data analysis.
    """
    if len(requests) > 100:
        raise HTTPException(
            status_code=400,
            detail="Batch size limited to 100 requests"
        )

    try:
        requests_data = [req.dict() for req in requests]
        task = batch_generate_insights.delay(requests_data)

        logger.info(f"Batch task submitted: {task.id} ({len(requests)} items)")

        return AsyncInsightResponse(
            task_id=task.id,
            status="submitted",
            message=f"Batch processing started for {len(requests)} insights."
        )

    except Exception as e:
        logger.error(f"Failed to submit batch task: {e}")
        raise HTTPException(status_code=500, detail=str(e))