import json
import httpx
from typing import Dict, Any
from .llm_base import LLMClient


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-pro"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def generate(
            self,
            prompt: str,
            response_schema: Dict[str, Any],
            temperature: float = 0.7,
            max_tokens: int = 1000
    ) -> str:
        """Call Gemini API with structured output guidance"""

        # Enhance prompt with schema instructions
        enhanced_prompt = f"""{prompt}

CRITICAL: You MUST respond with valid JSON matching this exact schema:
{json.dumps(response_schema, indent=2)}

Return ONLY the JSON object, no markdown formatting, no explanations."""

        payload = {
            "contents": [{
                "parts": [{
                    "text": enhanced_prompt
                }]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            data = response.json()

            # Extract text from Gemini response structure
            if "candidates" in data and len(data["candidates"]) > 0:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return content
            else:
                raise ValueError("No content in Gemini response")

    def get_model_name(self) -> str:
        return self.model
