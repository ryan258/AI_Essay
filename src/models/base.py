"""Abstract base class for AI models."""

from abc import ABC, abstractmethod
from typing import Tuple


class AIModel(ABC):
    """Abstract base class for AI model implementations.

    All model implementations should inherit from this class and implement
    the call() method.
    """

    def __init__(
        self,
        model_id: str,
        max_tokens: int = 1000,
        temperature: float = 1.0,
        retry_limit: int = 25
    ):
        """
        Initialize the AI model.

        Args:
            model_id: Model identifier
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-2.0)
            retry_limit: Maximum retry attempts on API errors
        """
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.retry_limit = retry_limit

    @abstractmethod
    def call(self, prompt: str) -> Tuple[bool, str, str]:
        """
        Call the AI model with a prompt.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Tuple of (success, response_text, error_message)
            - success: True if call succeeded, False otherwise
            - response_text: The model's response (empty string on failure)
            - error_message: Error details (empty string on success)
        """
        pass

    def __repr__(self) -> str:
        """String representation of the model."""
        return (
            f"{self.__class__.__name__}("
            f"model_id='{self.model_id}', "
            f"max_tokens={self.max_tokens}, "
            f"temperature={self.temperature})"
        )
