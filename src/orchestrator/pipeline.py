"""
Orchestrator Module - AI Pipeline.

The main orchestration pipeline that connects:
1. Natural language input
2. AI code generation
3. Code execution in Blender
4. Error handling and retry with AI fixes
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.ai.exceptions import AIProviderError
from src.ai.factory import ProviderFactory, get_provider
from src.ai.provider import AIProvider, GenerationResult, ProviderType
from src.executor.exceptions import RetryExhaustedError
from src.executor.history import ExecutionHistory, ExecutionStatus
from src.executor.retry import RetryConfig, RetryManager
from src.executor.safe_exec import SafeExecutor
from src.orchestrator.exceptions import (
    BlenderNotConnectedError,
)
from src.telemetry.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the AI pipeline."""

    # Provider settings
    provider: str = "gemini"
    model: str | None = None
    api_key: str | None = None

    # Retry settings
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0

    # Execution settings
    timeout: float = 30.0
    validate_syntax: bool = True

    # History settings
    max_history: int = 100


@dataclass
class PipelineResult:
    """Result from a complete pipeline execution."""

    success: bool
    code: str | None = None
    output: Any = None
    error: str | None = None

    # Metadata
    attempts: int = 0
    model_used: str | None = None
    tokens_used: int | None = None
    execution_time: float = 0.0

    # Context
    original_request: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class AIPipeline:
    """
    Main orchestration pipeline for AI-powered Blender interaction.

    This class coordinates:
    - AI provider selection and model switching
    - Code generation from natural language
    - Syntax validation
    - Execution via Blender bridge
    - Error handling with AI-powered fixes
    - Execution history tracking
    """

    def __init__(
        self,
        config: PipelineConfig | None = None,
        provider: AIProvider | None = None,
    ) -> None:
        """
        Initialize the AI pipeline.

        Args:
            config: Pipeline configuration. Uses defaults if None.
            provider: Pre-configured AI provider. Creates from config if None.
        """
        logger.debug("Initializing AI pipeline")

        self._config = config or PipelineConfig()

        # Initialize or use provided AI provider
        if provider is not None:
            self._provider = provider
        else:
            self._provider = self._create_provider()

        # Initialize retry manager
        retry_config = RetryConfig(
            max_attempts=self._config.max_retries,
            initial_delay=self._config.initial_delay,
            max_delay=self._config.max_delay,
            exponential_base=self._config.backoff_factor,
        )
        self._retry_manager = RetryManager(config=retry_config)

        # Initialize safe executor
        self._safe_executor = SafeExecutor()

        # Initialize execution history
        self._history = ExecutionHistory(max_records=self._config.max_history)

        # Blender client (lazy initialized)
        self._blender_client: Any = None

        logger.info(
            "AI pipeline initialized",
            extra={
                "provider": self._provider.provider_type.value,
                "model": self._provider.current_model,
                "max_retries": self._config.max_retries,
            },
        )

    def _create_provider(self) -> AIProvider:
        """Create an AI provider from configuration."""
        logger.debug(
            "Creating AI provider",
            extra={
                "provider": self._config.provider,
                "model": self._config.model,
            },
        )
        return get_provider(
            provider=self._config.provider,
            api_key=self._config.api_key,
            model=self._config.model,
        )

    @property
    def provider(self) -> AIProvider:
        """Return the current AI provider."""
        return self._provider

    @property
    def history(self) -> ExecutionHistory:
        """Return the execution history."""
        return self._history

    @property
    def config(self) -> PipelineConfig:
        """Return the pipeline configuration."""
        return self._config

    def set_provider(
        self,
        provider: str | ProviderType,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Switch to a different AI provider.

        Args:
            provider: Provider name or type.
            api_key: API key for the provider.
            model: Model to use.
        """
        logger.info(
            "Switching AI provider",
            extra={"provider": str(provider), "model": model},
        )
        self._provider = ProviderFactory.create(
            provider=provider,
            api_key=api_key,
            model=model,
        )

    def set_model(self, model: str) -> None:
        """
        Switch to a different model on the current provider.

        Args:
            model: Model name to switch to.
        """
        logger.info(
            "Switching model",
            extra={"model": model, "provider": self._provider.provider_type.value},
        )
        self._provider.model = model

    async def connect_blender(
        self,
        host: str = "localhost",
        port: int = 5005,
    ) -> bool:
        """
        Connect to a running Blender instance.

        Args:
            host: Blender server host.
            port: Blender server port.

        Returns:
            True if connection successful.
        """
        await asyncio.sleep(0)  # Yield to event loop
        logger.debug(
            "Connecting to Blender",
            extra={"host": host, "port": port},
        )

        try:
            from src.bridge.client import BlenderClient

            self._blender_client = BlenderClient(host=host, port=port)
            self._blender_client.connect()

            logger.info(
                "Connected to Blender",
                extra={"host": host, "port": port},
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to connect to Blender",
                extra={"host": host, "port": port, "error": str(e)},
            )
            self._blender_client = None
            return False

    def disconnect_blender(self) -> None:
        """Disconnect from Blender."""
        if self._blender_client is not None:
            logger.debug("Disconnecting from Blender")
            self._blender_client.disconnect()
            self._blender_client = None
            logger.info("Disconnected from Blender")

    @property
    def is_connected(self) -> bool:
        """Return True if connected to Blender."""
        return self._blender_client is not None and self._blender_client.is_connected

    async def execute(
        self,
        request: str,
        context: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """
        Execute a natural language request through the full pipeline.

        Pipeline stages:
        1. Generate code from natural language
        2. Validate syntax
        3. Execute in Blender
        4. On error: Fix with AI and retry

        Args:
            request: Natural language request.
            context: Optional Blender scene context.

        Returns:
            PipelineResult with execution outcome.
        """
        logger.info(
            "Starting pipeline execution",
            extra={"request_length": len(request), "has_context": context is not None},
        )

        start_time = datetime.now()

        # Validate connection
        if not self.is_connected:
            logger.error("Blender not connected")
            return PipelineResult(
                success=False,
                error="Blender is not connected. Call connect_blender() first.",
                original_request=request,
            )

        try:
            # Stage 1: Generate initial code
            generation_result = await self._generate_code(request, context)

            # Stage 2: Execute with retry loop
            code = generation_result.code
            result, attempts = await self._execute_with_fixes(
                code=code,
                original_request=request,
                context=context,
            )

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Record success in history
            self._history.add_record(
                user_request=request,
                code=code,
                status=ExecutionStatus.SUCCESS,
                model_used=generation_result.model_used,
                execution_time=execution_time,
                attempts=attempts,
            )

            logger.info(
                "Pipeline execution successful",
                extra={
                    "attempts": attempts,
                    "execution_time": execution_time,
                    "model": generation_result.model_used,
                },
            )

            return PipelineResult(
                success=True,
                code=code,
                output=result,
                attempts=attempts,
                model_used=generation_result.model_used,
                tokens_used=generation_result.total_tokens,
                execution_time=execution_time,
                original_request=request,
            )

        except RetryExhaustedError as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.error(
                "Pipeline failed: retries exhausted",
                extra={"attempts": e.attempts, "errors": len(e.errors)},
            )

            return PipelineResult(
                success=False,
                error=f"Execution failed after {e.attempts} attempts",
                attempts=e.attempts,
                execution_time=execution_time,
                original_request=request,
            )

        except AIProviderError as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.error(
                "Pipeline failed: AI provider error",
                extra={"error": str(e), "error_type": type(e).__name__},
            )

            return PipelineResult(
                success=False,
                error=f"AI error: {e}",
                execution_time=execution_time,
                original_request=request,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.error(
                "Pipeline failed: unexpected error",
                extra={"error": str(e), "error_type": type(e).__name__},
            )

            return PipelineResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                original_request=request,
            )

    async def _generate_code(
        self,
        request: str,
        context: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """Generate code from natural language request."""
        logger.debug("Generating code", extra={"request_length": len(request)})

        result = await self._provider.generate_code(request, context)

        # Validate syntax if enabled
        if self._config.validate_syntax:
            self._safe_executor.validate_syntax(result.code)

        logger.debug(
            "Code generated",
            extra={
                "code_length": len(result.code),
                "tokens": result.total_tokens,
            },
        )

        return result

    async def _execute_with_fixes(
        self,
        code: str,
        original_request: str,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> tuple[Any, int]:
        """Execute code with AI-powered error fixing."""

        async def execute_fn(current_code: str) -> dict[str, Any]:
            """Execute code in Blender and return result dict."""
            await asyncio.sleep(0)  # Yield to event loop
            if self._blender_client is None:
                raise BlenderNotConnectedError()

            result = self._blender_client.execute(current_code)
            return result

        async def fix_fn(failed_code: str, error: str) -> str:
            """Use AI to fix failed code."""
            logger.debug(
                "Requesting AI fix",
                extra={"code_length": len(failed_code), "error_length": len(error)},
            )

            fix_result = await self._provider.fix_code(
                code=failed_code,
                error=error,
                original_request=original_request,
            )

            # Validate fixed code syntax
            if self._config.validate_syntax:
                self._safe_executor.validate_syntax(fix_result.code)

            return fix_result.code

        return await self._retry_manager.execute_with_retry(
            execute_fn=execute_fn,
            fix_fn=fix_fn,
            code=code,
        )

    async def generate_only(
        self,
        request: str,
        context: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """
        Generate code without executing it.

        Useful for previewing code before execution.

        Args:
            request: Natural language request.
            context: Optional Blender scene context.

        Returns:
            GenerationResult with generated code.
        """
        logger.debug(
            "Generate only mode",
            extra={"request_length": len(request)},
        )
        return await self._generate_code(request, context)

    def get_available_providers(self) -> list[ProviderType]:
        """Return list of available AI providers."""
        return list(ProviderType)

    def get_available_models(self) -> list[str]:
        """Return list of available models for current provider."""
        return [m.name for m in self._provider.available_models]
