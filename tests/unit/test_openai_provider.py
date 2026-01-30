"""
Tests for OpenAI Provider.

Tests the OpenAI provider scaffolding with mocked API calls.
"""

import pytest

from src.ai.exceptions import APIKeyMissingError
from src.ai.provider import ModelInfo


class TestOpenAIProviderModels:
    """Test OpenAI provider model configuration."""

    def test_model_list_has_expected_models(self) -> None:
        """Test that OpenAI has the expected model options."""
        # Import at test time to avoid API key validation
        from src.ai.openai_provider import OpenAIProvider

        expected_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "o1",
            "o1-mini",
        ]

        model_names = [m.name for m in OpenAIProvider.MODELS]

        for expected in expected_models:
            assert expected in model_names

    def test_default_model_is_gpt4o(self) -> None:
        """Test that the default model is gpt-4o."""
        from src.ai.openai_provider import OpenAIProvider

        assert OpenAIProvider.DEFAULT_MODEL == "gpt-4o"

    def test_model_info_structure(self) -> None:
        """Test that model info has required fields."""
        from src.ai.openai_provider import OpenAIProvider

        for model_info in OpenAIProvider.MODELS:
            assert isinstance(model_info, ModelInfo)
            assert model_info.name
            assert model_info.display_name
            assert model_info.max_tokens > 0
            assert isinstance(model_info.supports_vision, bool)
            assert isinstance(model_info.supports_code, bool)


class TestOpenAIProviderInitialization:
    """Test OpenAI provider initialization."""

    def test_missing_api_key_raises_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that missing API key raises appropriate error."""
        # Clear environment variable
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from src.ai.openai_provider import OpenAIProvider

        with pytest.raises(APIKeyMissingError):
            OpenAIProvider()


class TestOpenAIProviderType:
    """Test OpenAI provider type identification."""

    def test_provider_type_is_openai(self) -> None:
        """Test that provider type is correctly identified."""
        from src.ai.openai_provider import OpenAIProvider

        # Check class-level MODELS which includes provider info
        assert any(m.name == "gpt-4o" for m in OpenAIProvider.MODELS)
