from fastapi import Depends
from app.config import get_settings, Settings
from app.clients.llm_base import LLMClient
from app.clients.mock_llm import MockLLMClient
from app.clients.gemini_client import GeminiClient
from app.clients.openai_client import OpenAIClient
from app.services.insight_service import InsightService


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """Dependency injection for LLM client based on configuration"""
    provider = settings.llm_provider.lower()

    if provider == "mock":
        return MockLLMClient()
    elif provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        return GeminiClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        return OpenAIClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def get_insight_service(
        llm_client: LLMClient = Depends(get_llm_client),
        settings: Settings = Depends(get_settings)
) -> InsightService:
    """Dependency injection for insight service"""
    return InsightService(llm_client=llm_client, settings=settings)
