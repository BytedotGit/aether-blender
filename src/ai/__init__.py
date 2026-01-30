"""
AI Module - __init__.py.

AI provider integrations for natural language to Blender code conversion.
"""

from src.ai.anthropic_provider import AnthropicProvider
from src.ai.exceptions import (
    AIProviderError,
    APIKeyInvalidError,
    APIKeyMissingError,
    CodeGenerationError,
    ContextTooLongError,
    ModelUnavailableError,
    ProviderConnectionError,
    ProviderNotFoundError,
    RateLimitError,
)
from src.ai.factory import ProviderFactory, get_provider
from src.ai.gemini_provider import GeminiProvider
from src.ai.openai_provider import OpenAIProvider
from src.ai.provider import (
    AIProvider,
    FixResult,
    GenerationResult,
    ModelInfo,
    ProviderType,
)

__all__ = [
    # Provider base
    "AIProvider",
    "GenerationResult",
    "FixResult",
    "ModelInfo",
    "ProviderType",
    # Providers
    "GeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    # Factory
    "ProviderFactory",
    "get_provider",
    # Exceptions
    "AIProviderError",
    "APIKeyMissingError",
    "APIKeyInvalidError",
    "RateLimitError",
    "ModelUnavailableError",
    "CodeGenerationError",
    "ContextTooLongError",
    "ProviderConnectionError",
    "ProviderNotFoundError",
]
