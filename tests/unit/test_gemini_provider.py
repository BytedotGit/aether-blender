"""
Unit Tests - Gemini Provider.

Tests for the Google Gemini AI provider integration.
Uses mocking to avoid actual API calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.exceptions import (
    APIKeyMissingError,
    ModelUnavailableError,
)
from src.ai.gemini_provider import GeminiProvider
from src.ai.provider import GenerationResult, ProviderType


class TestGeminiProviderInit:
    """Tests for GeminiProvider initialization."""

    def test_init_without_api_key_raises(self) -> None:
        """Test initialization without API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(APIKeyMissingError) as exc_info:
                GeminiProvider()

            assert "GEMINI_API_KEY" in str(exc_info.value)

    @patch("src.ai.gemini_provider.genai")
    def test_init_with_api_key_param(self, mock_genai: MagicMock) -> None:
        """Test initialization with API key parameter."""
        provider = GeminiProvider(api_key="test-key")

        mock_genai.configure.assert_called_once_with(api_key="test-key")
        assert provider.model == "gemini-2.0-flash"

    @patch("src.ai.gemini_provider.genai")
    @patch.dict("os.environ", {"GEMINI_API_KEY": "env-key"})
    def test_init_with_env_api_key(self, mock_genai: MagicMock) -> None:
        """Test initialization with API key from environment."""
        provider = GeminiProvider()

        mock_genai.configure.assert_called_once_with(api_key="env-key")
        assert provider.model == "gemini-2.0-flash"

    @patch("src.ai.gemini_provider.genai")
    def test_init_with_custom_model(self, mock_genai: MagicMock) -> None:
        """Test initialization with custom model."""
        provider = GeminiProvider(api_key="test-key", model="gemini-1.5-pro")

        assert provider.model == "gemini-1.5-pro"

    @patch("src.ai.gemini_provider.genai")
    def test_init_with_invalid_model_raises(self, mock_genai: MagicMock) -> None:
        """Test initialization with invalid model raises error."""
        with pytest.raises(ModelUnavailableError) as exc_info:
            GeminiProvider(api_key="test-key", model="invalid-model")

        assert "invalid-model" in str(exc_info.value)


class TestGeminiProviderProperties:
    """Tests for GeminiProvider properties."""

    @patch("src.ai.gemini_provider.genai")
    def test_provider_type(self, mock_genai: MagicMock) -> None:
        """Test provider_type returns GEMINI."""
        provider = GeminiProvider(api_key="test-key")
        assert provider.provider_type == ProviderType.GEMINI

    @patch("src.ai.gemini_provider.genai")
    def test_default_model(self, mock_genai: MagicMock) -> None:
        """Test default_model returns expected value."""
        provider = GeminiProvider(api_key="test-key")
        assert provider.default_model == "gemini-2.0-flash"

    @patch("src.ai.gemini_provider.genai")
    def test_available_models(self, mock_genai: MagicMock) -> None:
        """Test available_models returns list of models."""
        provider = GeminiProvider(api_key="test-key")
        models = provider.available_models

        assert len(models) == 4
        model_names = [m.name for m in models]
        assert "gemini-2.0-flash" in model_names
        assert "gemini-1.5-pro" in model_names
        assert "gemini-1.5-flash" in model_names

    @patch("src.ai.gemini_provider.genai")
    def test_change_model_reinitializes_client(self, mock_genai: MagicMock) -> None:
        """Test changing model reinitializes the client."""
        provider = GeminiProvider(api_key="test-key")
        initial_calls = mock_genai.GenerativeModel.call_count

        provider.model = "gemini-1.5-pro"

        # Should have called GenerativeModel again
        assert mock_genai.GenerativeModel.call_count > initial_calls


class TestGeminiProviderGenerateCode:
    """Tests for code generation."""

    @patch("src.ai.gemini_provider.genai")
    @pytest.mark.asyncio
    async def test_generate_code_success(self, mock_genai: MagicMock) -> None:
        """Test successful code generation."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "import bpy\nbpy.ops.mesh.primitive_cube_add()"
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=10,
            candidates_token_count=20,
            total_token_count=30,
        )

        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="test-key")
        result = await provider.generate_code("create a cube")

        assert isinstance(result, GenerationResult)
        assert "bpy.ops.mesh.primitive_cube_add" in result.code
        assert result.model_used == "gemini-2.0-flash"
        assert result.total_tokens == 30

    @patch("src.ai.gemini_provider.genai")
    @pytest.mark.asyncio
    async def test_generate_code_with_context(self, mock_genai: MagicMock) -> None:
        """Test code generation with context."""
        mock_response = MagicMock()
        mock_response.text = "import bpy"
        mock_response.usage_metadata = None

        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="test-key")
        context = {
            "scene_objects": ["Cube", "Camera"],
            "active_object": "Cube",
        }

        result = await provider.generate_code("move the cube", context=context)

        assert result.code == "import bpy"
        # Verify context was included in prompt
        call_args = mock_model.generate_content_async.call_args[0][0]
        assert "Scene Objects" in call_args or "Cube" in call_args


class TestGeminiProviderFixCode:
    """Tests for code fixing."""

    @patch("src.ai.gemini_provider.genai")
    @pytest.mark.asyncio
    async def test_fix_code_success(self, mock_genai: MagicMock) -> None:
        """Test successful code fixing."""
        mock_response = MagicMock()
        mock_response.text = "import bpy\ncube = bpy.data.objects.get('Cube')"
        mock_response.usage_metadata = None

        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="test-key")
        result = await provider.fix_code(
            code="cube = bpy.data.objects['Cube']",
            error="KeyError: 'Cube'",
            original_request="get the cube",
        )

        assert "get" in result.code
        assert result.model_used == "gemini-2.0-flash"


class TestGeminiProviderValidation:
    """Tests for connection validation."""

    @patch("src.ai.gemini_provider.genai")
    @pytest.mark.asyncio
    async def test_validate_connection_success(self, mock_genai: MagicMock) -> None:
        """Test successful connection validation."""
        mock_response = MagicMock()
        mock_response.text = "ok"

        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="test-key")
        result = await provider.validate_connection()

        assert result is True

    @patch("src.ai.gemini_provider.genai")
    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, mock_genai: MagicMock) -> None:
        """Test connection validation failure."""
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="test-key")
        result = await provider.validate_connection()

        assert result is False
