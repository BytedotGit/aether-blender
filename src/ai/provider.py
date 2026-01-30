"""
AI Module - Abstract Provider Base Class.

Defines the interface that all AI providers must implement.
Supports model selection for each provider.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.telemetry.logger import get_logger

logger = get_logger(__name__)


class ProviderType(Enum):
    """Supported AI provider types."""

    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


@dataclass
class ModelInfo:
    """Information about an AI model."""

    name: str
    display_name: str
    max_tokens: int
    supports_vision: bool = False
    supports_code: bool = True
    description: str = ""


@dataclass
class GenerationResult:
    """Result from code generation."""

    code: str
    model_used: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    raw_response: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FixResult:
    """Result from code fix attempt."""

    code: str
    model_used: str
    fix_explanation: str | None = None
    changes_made: list[str] = field(default_factory=list)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    All AI integrations (Gemini, OpenAI, Anthropic, Ollama) must
    inherit from this class and implement the abstract methods.
    """

    def __init__(self, model: str | None = None) -> None:
        """
        Initialize the AI provider.

        Args:
            model: The model to use. If None, uses the provider's default.
        """
        logger.debug(
            "Initializing AI provider",
            extra={"provider": self.provider_type.value, "model": model},
        )
        self._model = model or self.default_model
        self._validate_model(self._model)
        logger.debug(
            "AI provider initialized",
            extra={"provider": self.provider_type.value, "model": self._model},
        )

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type enum."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""
        pass

    @property
    @abstractmethod
    def available_models(self) -> list[ModelInfo]:
        """Return list of available models for this provider."""
        pass

    @property
    def model(self) -> str:
        """Return the currently selected model."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set the model, validating it's available."""
        logger.debug(
            "Changing model",
            extra={"provider": self.provider_type.value, "new_model": value},
        )
        self._validate_model(value)
        self._model = value

    def _validate_model(self, model: str) -> None:
        """Validate that the model is available for this provider."""
        from src.ai.exceptions import ModelUnavailableError

        available_names = [m.name for m in self.available_models]
        if model not in available_names:
            logger.error(
                "Invalid model selected",
                extra={
                    "model": model,
                    "available": available_names,
                },
            )
            raise ModelUnavailableError(model, available_names)

    def get_model_info(self, model_name: str | None = None) -> ModelInfo:
        """Get information about a specific model or the current model."""
        target = model_name or self._model
        for model_info in self.available_models:
            if model_info.name == target:
                return model_info
        from src.ai.exceptions import ModelUnavailableError

        raise ModelUnavailableError(target)

    @abstractmethod
    async def generate_code(
        self,
        user_request: str,
        context: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """
        Generate Blender Python code from natural language.

        Args:
            user_request: The user's natural language request.
            context: Optional context including scene info, history, etc.

        Returns:
            GenerationResult with the generated code and metadata.

        Raises:
            AIProviderError: If code generation fails.
        """
        pass

    @abstractmethod
    async def fix_code(
        self,
        code: str,
        error: str,
        original_request: str,
    ) -> FixResult:
        """
        Fix code that failed execution.

        Args:
            code: The code that failed.
            error: The error message from execution.
            original_request: The original user request.

        Returns:
            FixResult with the fixed code and explanation.

        Raises:
            AIProviderError: If code fixing fails.
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate that the provider connection is working.

        Returns:
            True if connection is valid, False otherwise.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self._model!r})"
