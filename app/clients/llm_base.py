from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMClient(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate(
            self,
            prompt: str,
            response_schema: Dict[str, Any],
            temperature: float = 0.7,
            max_tokens: int = 1000
    ) -> str:
        """
        Generate text from prompt.

        Returns: JSON string that should match response_schema
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier"""
        pass
