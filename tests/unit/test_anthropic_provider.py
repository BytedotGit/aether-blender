"""
Tests for Anthropic Provider.

Tests the Anthropic provider scaffolding with mocked API calls.
"""

import pytest

from src.ai.exceptions import APIKeyMissingError
from src.ai.provider import ModelInfo


class TestAnthropicProviderModels:
    """Test Anthropic provider model configuration."""

    def test_model_list_has_expected_models(self) -> None:
        """Test that Anthropic has the expected model options."""
        from src.ai.anthropic_provider import AnthropicProvider

        expected_models = [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

        model_names = [m.name for m in AnthropicProvider.MODELS]

        for expected in expected_models:
            assert expected in model_names

    def test_default_model_is_claude_sonnet_4(self) -> None:
        """Test that the default model is claude-sonnet-4."""
        from src.ai.anthropic_provider import AnthropicProvider

        assert AnthropicProvider.DEFAULT_MODEL == "claude-sonnet-4-20250514"

    def test_model_info_structure(self) -> None:
        """Test that model info has required fields."""
        from src.ai.anthropic_provider import AnthropicProvider

        for model_info in AnthropicProvider.MODELS:
            assert isinstance(model_info, ModelInfo)
            assert model_info.name
            assert model_info.display_name
            assert model_info.max_tokens > 0
            assert isinstance(model_info.supports_vision, bool)
            assert isinstance(model_info.supports_code, bool)


class TestAnthropicProviderInitialization:
    """Test Anthropic provider initialization."""

    def test_missing_api_key_raises_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that missing API key raises appropriate error."""
        # Clear environment variable
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from src.ai.anthropic_provider import AnthropicProvider

        with pytest.raises(APIKeyMissingError):
            AnthropicProvider()


class TestAnthropicProviderType:
    """Test Anthropic provider type identification."""

    def test_provider_type_models_include_claude(self) -> None:
        """Test that Anthropic models include Claude models."""
        from src.ai.anthropic_provider import AnthropicProvider

        model_names = [m.name for m in AnthropicProvider.MODELS]
        assert any("claude" in name for name in model_names)
