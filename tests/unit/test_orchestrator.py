"""
Tests for AI Pipeline Orchestrator.

Tests the orchestration pipeline configuration and basic functionality.
"""

import pytest

from src.orchestrator.exceptions import (
    BlenderNotConnectedError,
    ExecutionFailedError,
    OrchestratorError,
    PipelineError,
)
from src.orchestrator.pipeline import AIPipeline, PipelineConfig, PipelineResult


class TestPipelineConfig:
    """Test PipelineConfig dataclass."""

    def test_default_config_values(self) -> None:
        """Test that default config has expected values."""
        config = PipelineConfig()

        assert config.provider == "gemini"
        assert config.model is None
        assert config.api_key is None
        assert config.max_retries == 3
        assert config.initial_delay == pytest.approx(1.0)
        assert config.max_delay == pytest.approx(30.0)
        assert config.backoff_factor == pytest.approx(2.0)
        assert config.timeout == pytest.approx(30.0)
        assert config.validate_syntax is True
        assert config.max_history == 100

    def test_custom_config_values(self) -> None:
        """Test that custom config values are respected."""
        config = PipelineConfig(
            provider="openai",
            model="gpt-4o",
            max_retries=5,
            timeout=60.0,
        )

        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.max_retries == 5
        assert config.timeout == pytest.approx(60.0)


class TestPipelineResult:
    """Test PipelineResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a success result."""
        result = PipelineResult(
            success=True,
            code="print('hello')",
            output="hello",
            attempts=1,
        )

        assert result.success is True
        assert result.code == "print('hello')"
        assert result.output == "hello"
        assert result.error is None
        assert result.attempts == 1

    def test_failure_result(self) -> None:
        """Test creating a failure result."""
        result = PipelineResult(
            success=False,
            error="Connection failed",
            attempts=3,
        )

        assert result.success is False
        assert result.error == "Connection failed"
        assert result.code is None
        assert result.attempts == 3

    def test_result_has_timestamp(self) -> None:
        """Test that result has a timestamp."""
        result = PipelineResult(success=True)
        assert result.timestamp is not None


class TestOrchestratorExceptions:
    """Test orchestrator exception classes."""

    def test_orchestrator_error_base(self) -> None:
        """Test OrchestratorError base exception."""
        error = OrchestratorError("test error")
        assert str(error) == "test error"

    def test_pipeline_error_with_stage(self) -> None:
        """Test PipelineError with stage information."""
        error = PipelineError("generation failed", stage="generate")
        assert "[generate]" in str(error)
        assert "generation failed" in str(error)
        assert error.stage == "generate"

    def test_pipeline_error_without_stage(self) -> None:
        """Test PipelineError without stage information."""
        error = PipelineError("generic error")
        assert str(error) == "generic error"
        assert error.stage is None

    def test_blender_not_connected_error(self) -> None:
        """Test BlenderNotConnectedError."""
        error = BlenderNotConnectedError()
        assert "not connected" in str(error).lower()

    def test_execution_failed_error_with_details(self) -> None:
        """Test ExecutionFailedError with code and attempts."""
        error = ExecutionFailedError(
            message="Syntax error",
            code="print('bad",
            attempts=3,
        )

        assert "Syntax error" in str(error)
        assert error.code == "print('bad"
        assert error.attempts == 3


class TestAIPipelineIsConnected:
    """Test AIPipeline connection state."""

    def test_pipeline_not_connected_initially(
        self, mock_gemini_provider: object
    ) -> None:
        """Test that pipeline is not connected initially."""
        pipeline = AIPipeline(provider=mock_gemini_provider)  # type: ignore[arg-type]

        assert pipeline.is_connected is False

    def test_pipeline_get_available_providers(
        self, mock_gemini_provider: object
    ) -> None:
        """Test getting list of available providers."""
        pipeline = AIPipeline(provider=mock_gemini_provider)  # type: ignore[arg-type]

        providers = pipeline.get_available_providers()
        assert len(providers) > 0

    def test_pipeline_get_available_models(self, mock_gemini_provider: object) -> None:
        """Test getting list of available models."""
        pipeline = AIPipeline(provider=mock_gemini_provider)  # type: ignore[arg-type]

        models = pipeline.get_available_models()
        assert isinstance(models, list)
        assert "gemini-1.5-flash" in models


class TestAIPipelineConfiguration:
    """Test AIPipeline configuration."""

    def test_pipeline_uses_provided_config(self, mock_gemini_provider: object) -> None:
        """Test that pipeline uses provided configuration."""
        config = PipelineConfig(max_retries=5, timeout=60.0)
        pipeline = AIPipeline(config=config, provider=mock_gemini_provider)  # type: ignore[arg-type]

        assert pipeline.config.max_retries == 5
        assert pipeline.config.timeout == pytest.approx(60.0)

    def test_pipeline_uses_default_config(self, mock_gemini_provider: object) -> None:
        """Test that pipeline uses default config when not provided."""
        pipeline = AIPipeline(provider=mock_gemini_provider)  # type: ignore[arg-type]

        assert pipeline.config.max_retries == 3
        assert pipeline.config.provider == "gemini"

    def test_pipeline_exposes_provider(self, mock_gemini_provider: object) -> None:
        """Test that pipeline exposes the AI provider."""
        pipeline = AIPipeline(provider=mock_gemini_provider)  # type: ignore[arg-type]

        assert pipeline.provider is mock_gemini_provider

    def test_pipeline_exposes_history(self, mock_gemini_provider: object) -> None:
        """Test that pipeline exposes execution history."""
        pipeline = AIPipeline(provider=mock_gemini_provider)  # type: ignore[arg-type]

        assert pipeline.history is not None
