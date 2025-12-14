import json
import httpx
from typing import Dict, Any
from .llm_base import LLMClient


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def generate(
            self,
            prompt: str,
            response_schema: Dict[str, Any],
            temperature: float = 0.7,
            max_tokens: int = 1000
    ) -> str:
        """Call OpenAI API with JSON mode"""

        # Add schema to system message
        system_prompt = f"""You are a data insights analyst. You must respond with valid JSON matching this schema:
{json.dumps(response_schema, indent=2)}

Return ONLY valid JSON, no markdown formatting."""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content

    def get_model_name(self) -> str:
        return self.model
