"""
Tests for Provider Factory.

Tests the factory pattern for creating AI providers.
"""

import pytest

from src.ai.exceptions import APIKeyMissingError, ProviderNotFoundError
from src.ai.factory import ProviderFactory, get_provider
from src.ai.provider import AIProvider, ProviderType


class TestProviderFactory:
    """Test ProviderFactory class."""

    def test_factory_available_providers_initially_empty(self) -> None:
        """Test that factory starts with no registered providers."""
        # Clear any existing registrations
        ProviderFactory._PROVIDER_CLASSES.clear()

        providers = ProviderFactory.available_providers()
        assert providers == []

    def test_factory_register_provider(self) -> None:
        """Test registering a provider class."""
        # Clear registrations
        ProviderFactory._PROVIDER_CLASSES.clear()

        # Create a mock provider class
        class MockProvider(AIProvider):
            MODELS = []
            DEFAULT_MODEL = "test"

            def __init__(self, **kwargs: object) -> None:
                # Mock init - no setup needed
                pass

            @property
            def provider_type(self) -> ProviderType:
                return ProviderType.GEMINI

            @property
            def default_model(self) -> str:
                return "test"

            @property
            def available_models(self) -> list:
                return []

            async def generate_code(self, *args: object, **kwargs: object) -> object:
                # Mock implementation
                return None

            async def fix_code(self, *args: object, **kwargs: object) -> object:
                # Mock implementation
                return None

        ProviderFactory.register_provider(ProviderType.GEMINI, MockProvider)
        assert ProviderType.GEMINI in ProviderFactory._PROVIDER_CLASSES

    def test_factory_create_unknown_provider_raises(self) -> None:
        """Test that creating unknown provider raises error."""
        # Clear registrations
        ProviderFactory._PROVIDER_CLASSES.clear()

        with pytest.raises(ProviderNotFoundError):
            ProviderFactory.create("unknown_provider")

    def test_factory_is_available_returns_false_for_unknown(self) -> None:
        """Test is_available returns False for unknown providers."""
        result = ProviderFactory.is_available("totally_fake_provider")
        assert result is False

    def test_factory_is_available_checks_provider_type(self) -> None:
        """Test is_available accepts ProviderType enum."""
        # This should not raise, just return bool
        result = ProviderFactory.is_available(ProviderType.GEMINI)
        # Result depends on whether Gemini can be imported
        assert isinstance(result, bool)


class TestProviderFactoryAutoRegister:
    """Test auto-registration of providers."""

    def test_auto_register_gemini_when_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that Gemini provider can be auto-registered."""
        # Clear registrations
        ProviderFactory._PROVIDER_CLASSES.clear()

        # Try to auto-register
        ProviderFactory._auto_register(ProviderType.GEMINI)

        # Should be registered now (if gemini module is importable)
        assert ProviderType.GEMINI in ProviderFactory._PROVIDER_CLASSES


class TestGetProviderFunction:
    """Test the get_provider convenience function."""

    def test_get_provider_without_api_key_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_provider without API key raises error."""
        # Clear environment
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(APIKeyMissingError):
            get_provider("gemini")

    def test_get_provider_unknown_raises(self) -> None:
        """Test that get_provider with unknown provider raises error."""
        with pytest.raises(ProviderNotFoundError):
            get_provider("nonexistent_ai")
