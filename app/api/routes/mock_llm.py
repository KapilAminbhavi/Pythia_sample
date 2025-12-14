from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict
import time

router = APIRouter(prefix="/api/v1", tags=["mock"])


class MockLLMRequest(BaseModel):
    prompt: str
    response_format: Optional[Dict] = None
    temperature: float = 0.7
    max_tokens: int = 500


class MockLLMResponse(BaseModel):
    content: str
    model: str = "mock-llm-v1"
    usage: Dict
    finish_reason: str = "stop"


@router.post("/mock-llm", response_model=MockLLMResponse)
async def mock_llm_endpoint(request: MockLLMRequest):
    """
    Mock LLM endpoint for testing.
    Returns a plausible JSON response based on prompt.
    """
    # Simulate processing time
    time.sleep(0.5)

    # Generate mock response
    mock_content = {
        "summary": "This is a mock LLM response for testing purposes.",
        "severity": "medium",
        "confidence": 0.85,
        "recommended_actions": [
            "Action 1 based on analysis",
            "Action 2 for further investigation"
        ],
        "key_findings": [
            "Finding 1 from the data",
            "Finding 2 showing patterns"
        ]
    }

    import json
    return MockLLMResponse(
        content=json.dumps(mock_content),
        usage={
            "prompt_tokens": len(request.prompt.split()),
            "completion_tokens": 50,
            "total_tokens": len(request.prompt.split()) + 50
        }
    )
