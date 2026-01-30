"""
AI Module - Anthropic Claude Provider.

Integration with Anthropic's Claude API for Blender code generation.
Supports multiple Claude models with runtime selection.
"""

import os
from typing import Any

from dotenv import load_dotenv

from src.ai.exceptions import (
    APIKeyInvalidError,
    APIKeyMissingError,
    CodeGenerationError,
    ProviderConnectionError,
    RateLimitError,
)
from src.ai.prompts.system import (
    BLENDER_SYSTEM_PROMPT,
    get_fix_prompt,
    get_generation_prompt,
)
from src.ai.prompts.templates import extract_code_from_response
from src.ai.provider import (
    AIProvider,
    FixResult,
    GenerationResult,
    ModelInfo,
    ProviderType,
)
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# Environment variable for Anthropic API key
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
ANTHROPIC_MODEL_ENV = "ANTHROPIC_MODEL"


class AnthropicProvider(AIProvider):
    """
    Anthropic Claude provider for Blender code generation.

    Supports multiple Claude models:
    - claude-3-5-sonnet: Best balance of speed and capability (default)
    - claude-3-opus: Most capable, best for complex tasks
    - claude-3-sonnet: Balanced performance
    - claude-3-haiku: Fastest, most affordable
    """

    # Available Claude models
    MODELS = [
        ModelInfo(
            name="claude-sonnet-4-20250514",
            display_name="Claude Sonnet 4",
            max_tokens=200000,
            supports_vision=True,
            supports_code=True,
            description="Latest Claude Sonnet - excellent balance of speed and capability",
        ),
        ModelInfo(
            name="claude-3-5-sonnet-20241022",
            display_name="Claude 3.5 Sonnet",
            max_tokens=200000,
            supports_vision=True,
            supports_code=True,
            description="High capability with excellent coding skills",
        ),
        ModelInfo(
            name="claude-3-opus-20240229",
            display_name="Claude 3 Opus",
            max_tokens=200000,
            supports_vision=True,
            supports_code=True,
            description="Most capable Claude model for complex tasks",
        ),
        ModelInfo(
            name="claude-3-sonnet-20240229",
            display_name="Claude 3 Sonnet",
            max_tokens=200000,
            supports_vision=True,
            supports_code=True,
            description="Balanced performance and cost",
        ),
        ModelInfo(
            name="claude-3-haiku-20240307",
            display_name="Claude 3 Haiku",
            max_tokens=200000,
            supports_vision=True,
            supports_code=True,
            description="Fastest and most affordable Claude model",
        ),
    ]

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
            model: The model to use. If None, uses claude-sonnet-4.

        Raises:
            APIKeyMissingError: If no API key is provided or found in environment.
        """
        logger.debug(
            "Initializing Anthropic provider",
            extra={"model": model, "has_api_key": api_key is not None},
        )

        # Get API key from parameter or environment
        self._api_key = api_key or os.getenv(ANTHROPIC_API_KEY_ENV)

        if not self._api_key:
            logger.error("Anthropic API key not provided")
            raise APIKeyMissingError(
                "Anthropic API key not found. "
                f"Set {ANTHROPIC_API_KEY_ENV} environment variable or pass api_key."
            )

        # Initialize the Anthropic client (lazy import to avoid issues if not installed)
        self._client: Any = None
        self._initialize_client()

        # Initialize base class with model selection
        super().__init__(model=model)

        logger.info(
            "Anthropic provider initialized",
            extra={"model": self.current_model},
        )

    def _initialize_client(self) -> None:
        """Initialize the Anthropic client."""
        logger.debug("Initializing Anthropic client")
        try:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self._api_key)
            logger.debug("Anthropic client initialized successfully")
        except ImportError as e:
            logger.error("Anthropic package not installed", extra={"error": str(e)})
            raise ProviderConnectionError(
                "Anthropic package not installed. Run: pip install anthropic"
            ) from e
        except Exception as e:
            logger.error(
                "Failed to initialize Anthropic client", extra={"error": str(e)}
            )
            raise ProviderConnectionError(f"Failed to initialize Anthropic: {e}") from e

    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.ANTHROPIC

    @property
    def default_model(self) -> str:
        """Return the default model name."""
        return self.DEFAULT_MODEL

    def available_models(self) -> list[ModelInfo]:
        """Return list of available models for this provider."""
        return self.MODELS.copy()

    def _on_model_change(self) -> None:
        """Handle model change - no special handling needed for Anthropic."""
        logger.debug(
            "Model changed",
            extra={"new_model": self.current_model},
        )

    async def generate_code(
        self,
        request: str,
        context: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """
        Generate Blender Python code from a natural language request.

        Args:
            request: The user's natural language request.
            context: Optional context about the current Blender scene.

        Returns:
            GenerationResult with the generated code.

        Raises:
            CodeGenerationError: If code generation fails.
            RateLimitError: If rate limited by API.
        """
        logger.debug(
            "Generating code with Anthropic",
            extra={
                "request_length": len(request),
                "has_context": context is not None,
                "model": self.current_model,
            },
        )

        try:
            # Build the prompt
            user_prompt = get_generation_prompt(request, context)

            # Call Anthropic API
            response = self._client.messages.create(
                model=self.current_model,
                system=BLENDER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.2,
                max_tokens=4096,
            )

            # Extract response content
            raw_response = response.content[0].text if response.content else ""
            code = extract_code_from_response(raw_response)

            # Build result with usage info
            result = GenerationResult(
                code=code,
                model_used=self.current_model,
                prompt_tokens=response.usage.input_tokens if response.usage else None,
                completion_tokens=(
                    response.usage.output_tokens if response.usage else None
                ),
                total_tokens=(
                    (response.usage.input_tokens + response.usage.output_tokens)
                    if response.usage
                    else None
                ),
                raw_response=raw_response,
            )

            logger.info(
                "Code generated successfully",
                extra={
                    "code_length": len(code),
                    "tokens_used": result.total_tokens,
                },
            )

            return result

        except Exception as e:
            error_str = str(e).lower()

            # Check for rate limiting
            if "rate" in error_str and "limit" in error_str:
                logger.warning("Rate limited by Anthropic", extra={"error": str(e)})
                raise RateLimitError(f"Anthropic rate limit exceeded: {e}") from e

            # Check for invalid API key
            if "invalid" in error_str and ("key" in error_str or "auth" in error_str):
                logger.error("Invalid Anthropic API key")
                raise APIKeyInvalidError("Anthropic API key is invalid") from e

            # Generic error
            logger.error(
                "Code generation failed",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise CodeGenerationError(f"Anthropic generation failed: {e}") from e

    async def fix_code(
        self,
        code: str,
        error: str,
        original_request: str,
    ) -> FixResult:
        """
        Attempt to fix code that failed to execute.

        Args:
            code: The code that failed.
            error: The error message from execution.
            original_request: The original user request.

        Returns:
            FixResult with the fixed code.

        Raises:
            CodeGenerationError: If fix generation fails.
        """
        logger.debug(
            "Fixing code with Anthropic",
            extra={
                "code_length": len(code),
                "error_length": len(error),
                "model": self.current_model,
            },
        )

        try:
            # Build the fix prompt
            fix_prompt = get_fix_prompt(code, error, original_request)

            # Call Anthropic API
            response = self._client.messages.create(
                model=self.current_model,
                system=BLENDER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": fix_prompt}],
                temperature=0.1,
                max_tokens=4096,
            )

            # Extract response content
            raw_response = response.content[0].text if response.content else ""
            fixed_code = extract_code_from_response(raw_response)

            result = FixResult(
                code=fixed_code,
                model_used=self.current_model,
                prompt_tokens=response.usage.input_tokens if response.usage else None,
                completion_tokens=(
                    response.usage.output_tokens if response.usage else None
                ),
            )

            logger.info(
                "Code fixed successfully",
                extra={"fixed_code_length": len(fixed_code)},
            )

            return result

        except Exception as e:
            logger.error(
                "Code fix failed",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise CodeGenerationError(f"Anthropic fix failed: {e}") from e

    async def validate_connection(self) -> bool:
        """
        Validate that the API connection is working.

        Returns:
            True if connection is valid, False otherwise.
        """
        logger.debug("Validating Anthropic connection")
        try:
            # Make a minimal API call to verify connection
            response = self._client.messages.create(
                model=self.current_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            is_valid = bool(response.content)
            logger.info("Anthropic connection validated", extra={"valid": is_valid})
            return is_valid
        except Exception as e:
            logger.error(
                "Anthropic connection validation failed",
                extra={"error": str(e)},
            )
            return False
