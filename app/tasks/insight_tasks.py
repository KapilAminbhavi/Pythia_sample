from celery import Task
from app.celery_app import celery_app
from app.services.insight_service import InsightService
from app.clients.llm_base import LLMClient
from app.clients.mock_llm import MockLLMClient
from app.clients.gemini_client import GeminiClient
from app.clients.openai_client import OpenAIClient
from app.database.connection import db
from app.repositories.insight_repository import InsightRepository
from app.models.schemas import InsightRequest, InsightResponse
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class InsightTask(Task):
    """Base task with LLM client initialization"""
    _llm_client = None

    @property
    def llm_client(self) -> LLMClient:
        if self._llm_client is None:
            settings = get_settings()
            provider = settings.llm_provider.lower()

            if provider == "mock":
                self._llm_client = MockLLMClient()
            elif provider == "gemini":
                self._llm_client = GeminiClient(
                    api_key=settings.gemini_api_key,
                    model=settings.gemini_model
                )
            elif provider == "openai":
                self._llm_client = OpenAIClient(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model
                )
            else:
                raise ValueError(f"Unknown LLM provider: {provider}")

        return self._llm_client


@celery_app.task(
    bind=True,
    base=InsightTask,
    name='app.tasks.insight_tasks.generate_insight_async',
    max_retries=3,
    default_retry_delay=60
)
def generate_insight_async(self, request_data: dict) -> dict:
    """
    Asynchronous insight generation task.

    This runs in a Celery worker, allowing the API to return immediately.

    Args:
        request_data: Dictionary representation of InsightRequest

    Returns:
        Dictionary representation of InsightResponse
    """
    try:
        logger.info(f"Starting async insight generation: {request_data.get('user_id')}")

        # Parse request
        request = InsightRequest(**request_data)

        # Get LLM client from task
        settings = get_settings()
        service = InsightService(
            llm_client=self.llm_client,
            settings=settings
        )

        # Generate insight (this is async, so we need to run it)
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(service.generate_insight(request))

        # Save to database
        session = db.get_session()
        try:
            repo = InsightRepository(session)
            repo.create(result)
            logger.info(f"Async insight saved: {result.insight_id}")
        finally:
            session.close()

        return result.dict()

    except Exception as e:
        logger.error(f"Async insight generation failed: {e}")
        # Retry on failure
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=InsightTask,
    name='app.tasks.insight_tasks.batch_generate_insights'
)
def batch_generate_insights(self, requests_data: list) -> dict:
    """
    Process multiple insights in batch.
    Useful for bulk data processing.

    Args:
        requests_data: List of InsightRequest dictionaries

    Returns:
        Summary of batch processing
    """
    logger.info(f"Starting batch processing: {len(requests_data)} insights")

    results = {
        'total': len(requests_data),
        'successful': 0,
        'failed': 0,
        'insight_ids': []
    }

    settings = get_settings()
    service = InsightService(
        llm_client=self.llm_client,
        settings=settings
    )

    for request_data in requests_data:
        try:
            request = InsightRequest(**request_data)

            import asyncio
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(service.generate_insight(request))

            # Save to database
            session = db.get_session()
            try:
                repo = InsightRepository(session)
                repo.create(result)
            finally:
                session.close()

            results['successful'] += 1
            results['insight_ids'].append(str(result.insight_id))

        except Exception as e:
            logger.error(f"Batch item failed: {e}")
            results['failed'] += 1

    logger.info(f"Batch complete: {results['successful']}/{results['total']} successful")
    return results


@celery_app.task(name='app.tasks.insight_tasks.cleanup_old_insights')
def cleanup_old_insights(days_old: int = 90):
    """
    Background task to clean up old insights.
    Run this via Celery Beat for scheduled cleanup.

    Args:
        days_old: Delete insights older than this many days
    """
    from datetime import datetime, timedelta

    logger.info(f"Starting cleanup of insights older than {days_old} days")

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

    session = db.get_session()
    try:
        from app.models.database import Insight
        deleted_count = session.query(Insight).filter(
            Insight.created_at < cutoff_date
        ).delete()

        session.commit()
        logger.info(f"Cleanup complete: {deleted_count} insights deleted")

        return {
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Cleanup failed: {e}")
        raise
    finally:
        session.close()