"""
AI Module - OpenAI Provider.

Integration with OpenAI's GPT API for Blender code generation.
Supports multiple GPT models with runtime selection.
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

# Environment variable for OpenAI API key
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_MODEL_ENV = "OPENAI_MODEL"


class OpenAIProvider(AIProvider):
    """
    OpenAI GPT provider for Blender code generation.

    Supports multiple GPT models:
    - gpt-4o: Most capable model, multimodal
    - gpt-4o-mini: Fast and affordable
    - gpt-4-turbo: High capability with vision
    - o1: Advanced reasoning model
    - o1-mini: Fast reasoning model
    """

    # Available OpenAI models
    MODELS = [
        ModelInfo(
            name="gpt-4o",
            display_name="GPT-4o",
            max_tokens=128000,
            supports_vision=True,
            supports_code=True,
            description="Most capable model, multimodal with vision support",
        ),
        ModelInfo(
            name="gpt-4o-mini",
            display_name="GPT-4o Mini",
            max_tokens=128000,
            supports_vision=True,
            supports_code=True,
            description="Fast and affordable for everyday tasks",
        ),
        ModelInfo(
            name="gpt-4-turbo",
            display_name="GPT-4 Turbo",
            max_tokens=128000,
            supports_vision=True,
            supports_code=True,
            description="High capability with vision support",
        ),
        ModelInfo(
            name="o1",
            display_name="o1",
            max_tokens=200000,
            supports_vision=False,
            supports_code=True,
            description="Advanced reasoning model for complex tasks",
        ),
        ModelInfo(
            name="o1-mini",
            display_name="o1-mini",
            max_tokens=128000,
            supports_vision=False,
            supports_code=True,
            description="Fast reasoning model",
        ),
    ]

    DEFAULT_MODEL = "gpt-4o"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            model: The model to use. If None, uses gpt-4o.

        Raises:
            APIKeyMissingError: If no API key is provided or found in environment.
        """
        logger.debug(
            "Initializing OpenAI provider",
            extra={"model": model, "has_api_key": api_key is not None},
        )

        # Get API key from parameter or environment
        self._api_key = api_key or os.getenv(OPENAI_API_KEY_ENV)

        if not self._api_key:
            logger.error("OpenAI API key not provided")
            raise APIKeyMissingError(
                "OpenAI API key not found. "
                f"Set {OPENAI_API_KEY_ENV} environment variable or pass api_key parameter."
            )

        # Initialize the OpenAI client (lazy import to avoid issues if not installed)
        self._client: Any = None
        self._initialize_client()

        # Initialize base class with model selection
        super().__init__(model=model)

        logger.info(
            "OpenAI provider initialized",
            extra={"model": self.current_model},
        )

    def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        logger.debug("Initializing OpenAI client")
        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
            logger.debug("OpenAI client initialized successfully")
        except ImportError as e:
            logger.error("OpenAI package not installed", extra={"error": str(e)})
            raise ProviderConnectionError(
                "OpenAI package not installed. Run: pip install openai"
            ) from e
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", extra={"error": str(e)})
            raise ProviderConnectionError(f"Failed to initialize OpenAI: {e}") from e

    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.OPENAI

    @property
    def default_model(self) -> str:
        """Return the default model name."""
        return self.DEFAULT_MODEL

    def available_models(self) -> list[ModelInfo]:
        """Return list of available models for this provider."""
        return self.MODELS.copy()

    def _on_model_change(self) -> None:
        """Handle model change - no special handling needed for OpenAI."""
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
            "Generating code with OpenAI",
            extra={
                "request_length": len(request),
                "has_context": context is not None,
                "model": self.current_model,
            },
        )

        try:
            # Build the prompt
            user_prompt = get_generation_prompt(request, context)

            # Call OpenAI API
            response = self._client.chat.completions.create(
                model=self.current_model,
                messages=[
                    {"role": "system", "content": BLENDER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=4096,
            )

            # Extract response content
            raw_response = response.choices[0].message.content or ""
            code = extract_code_from_response(raw_response)

            # Build result with usage info
            usage = response.usage
            result = GenerationResult(
                code=code,
                model_used=self.current_model,
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
                total_tokens=usage.total_tokens if usage else None,
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
                logger.warning("Rate limited by OpenAI", extra={"error": str(e)})
                raise RateLimitError(f"OpenAI rate limit exceeded: {e}") from e

            # Check for invalid API key
            if "invalid" in error_str and "key" in error_str:
                logger.error("Invalid OpenAI API key")
                raise APIKeyInvalidError("OpenAI API key is invalid") from e

            # Generic error
            logger.error(
                "Code generation failed",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise CodeGenerationError(f"OpenAI generation failed: {e}") from e

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
            "Fixing code with OpenAI",
            extra={
                "code_length": len(code),
                "error_length": len(error),
                "model": self.current_model,
            },
        )

        try:
            # Build the fix prompt
            fix_prompt = get_fix_prompt(code, error, original_request)

            # Call OpenAI API
            response = self._client.chat.completions.create(
                model=self.current_model,
                messages=[
                    {"role": "system", "content": BLENDER_SYSTEM_PROMPT},
                    {"role": "user", "content": fix_prompt},
                ],
                temperature=0.1,
                max_tokens=4096,
            )

            # Extract response content
            raw_response = response.choices[0].message.content or ""
            fixed_code = extract_code_from_response(raw_response)

            usage = response.usage
            result = FixResult(
                code=fixed_code,
                model_used=self.current_model,
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
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
            raise CodeGenerationError(f"OpenAI fix failed: {e}") from e

    async def validate_connection(self) -> bool:
        """
        Validate that the API connection is working.

        Returns:
            True if connection is valid, False otherwise.
        """
        logger.debug("Validating OpenAI connection")
        try:
            # Make a minimal API call to verify connection
            response = self._client.chat.completions.create(
                model=self.current_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            is_valid = response.choices[0].message.content is not None
            logger.info("OpenAI connection validated", extra={"valid": is_valid})
            return is_valid
        except Exception as e:
            logger.error(
                "OpenAI connection validation failed",
                extra={"error": str(e)},
            )
            return False
