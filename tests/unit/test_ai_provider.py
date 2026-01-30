"""
Unit Tests - AI Provider Base Class.

Tests for the abstract provider interface, model validation,
and common provider functionality.
"""

import pytest

from src.ai.exceptions import ModelUnavailableError
from src.ai.provider import (
    AIProvider,
    FixResult,
    GenerationResult,
    ModelInfo,
    ProviderType,
)


class MockProvider(AIProvider):
    """Mock provider for testing the base class."""

    MOCK_MODELS = [
        ModelInfo(
            name="mock-model-1",
            display_name="Mock Model 1",
            max_tokens=4096,
        ),
        ModelInfo(
            name="mock-model-2",
            display_name="Mock Model 2",
            max_tokens=8192,
            supports_vision=True,
        ),
    ]

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GEMINI  # Use existing enum value for test

    @property
    def default_model(self) -> str:
        return "mock-model-1"

    @property
    def available_models(self) -> list[ModelInfo]:
        return self.MOCK_MODELS.copy()

    async def generate_code(self, user_request, context=None):
        return GenerationResult(
            code=f"# Generated for: {user_request}",
            model_used=self._model,
        )

    async def fix_code(self, code, error, original_request):
        return FixResult(
            code=code.replace("broken", "fixed"),
            model_used=self._model,
        )

    async def validate_connection(self):
        return True


class TestAIProviderInit:
    """Tests for AIProvider initialization."""

    def test_init_with_default_model(self) -> None:
        """Test initialization with default model."""
        provider = MockProvider()
        assert provider.model == "mock-model-1"

    def test_init_with_custom_model(self) -> None:
        """Test initialization with specified model."""
        provider = MockProvider(model="mock-model-2")
        assert provider.model == "mock-model-2"

    def test_init_with_invalid_model_raises(self) -> None:
        """Test initialization with invalid model raises error."""
        with pytest.raises(ModelUnavailableError) as exc_info:
            MockProvider(model="nonexistent-model")

        assert "nonexistent-model" in str(exc_info.value)
        assert "mock-model-1" in str(exc_info.value)


class TestAIProviderModels:
    """Tests for model selection and info."""

    def test_available_models_returns_list(self) -> None:
        """Test that available_models returns a list."""
        provider = MockProvider()
        models = provider.available_models
        assert isinstance(models, list)
        assert len(models) == 2

    def test_get_model_info_current(self) -> None:
        """Test getting info about current model."""
        provider = MockProvider()
        info = provider.get_model_info()
        assert info.name == "mock-model-1"
        assert info.max_tokens == 4096

    def test_get_model_info_specific(self) -> None:
        """Test getting info about specific model."""
        provider = MockProvider()
        info = provider.get_model_info("mock-model-2")
        assert info.name == "mock-model-2"
        assert info.supports_vision is True

    def test_get_model_info_invalid_raises(self) -> None:
        """Test getting info about invalid model raises."""
        provider = MockProvider()
        with pytest.raises(ModelUnavailableError):
            provider.get_model_info("invalid")

    def test_change_model(self) -> None:
        """Test changing model after initialization."""
        provider = MockProvider()
        assert provider.model == "mock-model-1"
        provider.model = "mock-model-2"
        assert provider.model == "mock-model-2"

    def test_change_to_invalid_model_raises(self) -> None:
        """Test changing to invalid model raises."""
        provider = MockProvider()
        with pytest.raises(ModelUnavailableError):
            provider.model = "invalid-model"


class TestAIProviderOperations:
    """Tests for provider operations."""

    @pytest.mark.asyncio
    async def test_generate_code_returns_result(self) -> None:
        """Test generate_code returns GenerationResult."""
        provider = MockProvider()
        result = await provider.generate_code("create a cube")

        assert isinstance(result, GenerationResult)
        assert "create a cube" in result.code
        assert result.model_used == "mock-model-1"

    @pytest.mark.asyncio
    async def test_fix_code_returns_result(self) -> None:
        """Test fix_code returns FixResult."""
        provider = MockProvider()
        result = await provider.fix_code(
            code="broken code",
            error="SyntaxError",
            original_request="make cube",
        )

        assert isinstance(result, FixResult)
        assert "fixed" in result.code
        assert result.model_used == "mock-model-1"

    @pytest.mark.asyncio
    async def test_validate_connection(self) -> None:
        """Test validate_connection returns bool."""
        provider = MockProvider()
        result = await provider.validate_connection()
        assert result is True


class TestProviderRepr:
    """Tests for provider string representation."""

    def test_repr(self) -> None:
        """Test __repr__ output."""
        provider = MockProvider()
        repr_str = repr(provider)
        assert "MockProvider" in repr_str
        assert "mock-model-1" in repr_str
