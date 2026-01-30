"""
AI Module - Provider Factory.

Factory for creating AI providers by name or type.
Handles provider registration and instantiation.
"""

from typing import Any

from src.ai.exceptions import ProviderNotFoundError
from src.ai.provider import AIProvider, ProviderType
from src.telemetry.logger import get_logger

logger = get_logger(__name__)


class ProviderFactory:
    """
    Factory for creating AI provider instances.

    Supports creating providers by name or ProviderType enum.
    Handles API key injection and model selection.
    """

    # Registry of provider types to their implementation classes
    _PROVIDER_CLASSES: dict[ProviderType, type[AIProvider]] = {}

    @classmethod
    def register_provider(
        cls, provider_type: ProviderType, provider_class: type[AIProvider]
    ) -> None:
        """
        Register a provider class for a given type.

        Args:
            provider_type: The provider type enum.
            provider_class: The provider class to register.
        """
        logger.debug(
            "Registering provider",
            extra={
                "provider_type": provider_type.value,
                "provider_class": provider_class.__name__,
            },
        )
        cls._PROVIDER_CLASSES[provider_type] = provider_class

    @classmethod
    def create(
        cls,
        provider: str | ProviderType,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> AIProvider:
        """
        Create an AI provider instance.

        Args:
            provider: Provider name (str) or ProviderType enum.
            api_key: API key for the provider. If None, uses environment variable.
            model: Model name to use. If None, uses provider default.
            **kwargs: Additional arguments to pass to the provider constructor.

        Returns:
            Configured AI provider instance.

        Raises:
            ProviderNotFoundError: If the provider is not registered or unknown.
        """
        logger.debug(
            "Creating provider",
            extra={
                "provider": str(provider),
                "has_api_key": api_key is not None,
                "model": model,
            },
        )

        # Convert string to ProviderType if needed
        if isinstance(provider, str):
            try:
                provider_type = ProviderType(provider.lower())
            except ValueError as e:
                logger.error(
                    "Unknown provider name",
                    extra={"provider": provider},
                )
                raise ProviderNotFoundError(
                    f"Unknown provider: {provider}. "
                    f"Available: {[p.value for p in ProviderType]}"
                ) from e
        else:
            provider_type = provider

        # Check if provider is registered
        if provider_type not in cls._PROVIDER_CLASSES:
            # Try to auto-register known providers
            cls._auto_register(provider_type)

        if provider_type not in cls._PROVIDER_CLASSES:
            logger.error(
                "Provider not registered",
                extra={"provider_type": provider_type.value},
            )
            raise ProviderNotFoundError(
                f"Provider {provider_type.value} is not registered. "
                "Make sure the provider module is imported."
            )

        # Create the provider instance
        provider_class = cls._PROVIDER_CLASSES[provider_type]

        try:
            # Build kwargs for provider constructor
            provider_kwargs: dict[str, Any] = {"model": model, **kwargs}
            if api_key is not None:
                provider_kwargs["api_key"] = api_key

            instance = provider_class(**provider_kwargs)
            logger.info(
                "Provider created successfully",
                extra={
                    "provider_type": provider_type.value,
                    "model": instance.current_model,
                },
            )
            return instance
        except Exception as e:
            logger.error(
                "Failed to create provider",
                extra={
                    "provider_type": provider_type.value,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

    @classmethod
    def _auto_register(cls, provider_type: ProviderType) -> None:
        """
        Attempt to auto-register a provider by importing its module.

        Args:
            provider_type: The provider type to register.
        """
        logger.debug(
            "Attempting auto-registration",
            extra={"provider_type": provider_type.value},
        )

        try:
            if provider_type == ProviderType.GEMINI:
                from src.ai.gemini_provider import GeminiProvider

                cls.register_provider(ProviderType.GEMINI, GeminiProvider)

            elif provider_type == ProviderType.OPENAI:
                from src.ai.openai_provider import OpenAIProvider

                cls.register_provider(ProviderType.OPENAI, OpenAIProvider)

            elif provider_type == ProviderType.ANTHROPIC:
                from src.ai.anthropic_provider import AnthropicProvider

                cls.register_provider(ProviderType.ANTHROPIC, AnthropicProvider)

            elif provider_type == ProviderType.OLLAMA:
                logger.warning(
                    "Ollama provider not yet implemented",
                    extra={"provider_type": provider_type.value},
                )

            logger.debug(
                "Auto-registration successful",
                extra={"provider_type": provider_type.value},
            )

        except ImportError as e:
            logger.warning(
                "Failed to auto-register provider",
                extra={"provider_type": provider_type.value, "error": str(e)},
            )

    @classmethod
    def available_providers(cls) -> list[ProviderType]:
        """
        Return list of available (registered) providers.

        Returns:
            List of registered ProviderType enums.
        """
        return list(cls._PROVIDER_CLASSES.keys())

    @classmethod
    def is_available(cls, provider: str | ProviderType) -> bool:
        """
        Check if a provider is available.

        Args:
            provider: Provider name or type to check.

        Returns:
            True if provider can be created, False otherwise.
        """
        try:
            if isinstance(provider, str):
                provider_type = ProviderType(provider.lower())
            else:
                provider_type = provider

            # Try to auto-register if not already registered
            if provider_type not in cls._PROVIDER_CLASSES:
                cls._auto_register(provider_type)

            return provider_type in cls._PROVIDER_CLASSES

        except ValueError:
            return False


def get_provider(
    provider: str = "gemini",
    api_key: str | None = None,
    model: str | None = None,
    **kwargs: Any,
) -> AIProvider:
    """
    Convenience function to get an AI provider.

    Args:
        provider: Provider name (gemini, openai, anthropic, ollama).
        api_key: API key for the provider.
        model: Model name to use.
        **kwargs: Additional provider arguments.

    Returns:
        Configured AI provider instance.
    """
    return ProviderFactory.create(
        provider=provider,
        api_key=api_key,
        model=model,
        **kwargs,
    )
