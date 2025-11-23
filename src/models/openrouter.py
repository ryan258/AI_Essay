"""OpenRouter AI model implementation."""

import os
from typing import Tuple
from openai import OpenAI

from .base import AIModel


# Model mappings removed in favor of direct model ID usage


class OpenRouterModel(AIModel):
    """OpenRouter AI model implementation.

    Provides access to multiple AI models (Claude, GPT, Gemini, Grok)
    through the unified OpenRouter API.
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        model_name: str,
        api_key: str = None,
        max_tokens: int = 1000,
        temperature: float = 1.0,
        retry_limit: int = 25,
        system_message: str = "You are a helpful assistant."
    ):
        """
        Initialize OpenRouter model.

        Args:
            model_name: OpenRouter model ID (e.g., 'anthropic/claude-3-opus')
            api_key: OpenRouter API key (if None, reads from env)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-2.0)
            retry_limit: Maximum retry attempts on API errors
            system_message: System message for the model

        Raises:
            ValueError: If API key is missing
        """
        # Use model_name directly as model_id
        super().__init__(model_name, max_tokens, temperature, retry_limit)

        self.model_name = model_name
        self.system_message = system_message

        # Get API key
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not found. "
                "Set OPENROUTER_API_KEY environment variable or pass api_key parameter."
            )

        # Initialize client (reused across calls)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.OPENROUTER_BASE_URL
        )

        # Lazy-initialize async client when needed
        self._async_client = None

    def call(self, prompt: str) -> Tuple[bool, str, str]:
        """
        Call the OpenRouter model with a prompt.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Tuple of (success, response_text, error_message)
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return True, completion.choices[0].message.content, ""

        except Exception as e:
            return False, "", f"API Error: {str(e)}"

    async def acall(self, prompt: str) -> Tuple[bool, str, str]:
        """
        Async call to the OpenRouter model with a prompt.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Tuple of (success, response_text, error_message)
        """
        from openai import AsyncOpenAI

        # Lazy-initialize async client on first use (reused for subsequent calls)
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.OPENROUTER_BASE_URL
            )

        try:
            completion = await self._async_client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return True, completion.choices[0].message.content, ""

        except Exception as e:
            return False, "", f"API Error: {str(e)}"

    def __repr__(self) -> str:
        """String representation of the model."""
        return (
            f"OpenRouterModel("
            f"model_name='{self.model_name}', "
            f"max_tokens={self.max_tokens}, "
            f"temperature={self.temperature})"
        )
