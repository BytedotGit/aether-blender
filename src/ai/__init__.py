"""
AI Module - __init__.py.

AI provider integrations for natural language to Blender code conversion.
"""

from src.ai.exceptions import (
    AIProviderError,
    APIKeyInvalidError,
    APIKeyMissingError,
    CodeGenerationError,
    ContextTooLongError,
    ModelUnavailableError,
    ProviderConnectionError,
    RateLimitError,
)
from src.ai.gemini_provider import GeminiProvider
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
    # Exceptions
    "AIProviderError",
    "APIKeyMissingError",
    "APIKeyInvalidError",
    "RateLimitError",
    "ModelUnavailableError",
    "CodeGenerationError",
    "ContextTooLongError",
    "ProviderConnectionError",
]
