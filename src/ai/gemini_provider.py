"""
AI Module - Google Gemini Provider.

Integration with Google's Gemini API for Blender code generation.
Supports multiple Gemini models with runtime selection.
"""

import os
from typing import Any

import google.generativeai as genai
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

# Environment variable for Gemini API key
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_MODEL_ENV = "GEMINI_MODEL"


class GeminiProvider(AIProvider):
    """
    Google Gemini AI provider for Blender code generation.

    Supports multiple Gemini models:
    - gemini-2.0-flash: Fast, efficient model (default)
    - gemini-1.5-pro: Most capable model
    - gemini-1.5-flash: Balanced speed and quality
    - gemini-2.0-flash-lite: Fastest, lightweight model
    """

    # Available Gemini models
    MODELS = [
        ModelInfo(
            name="gemini-2.0-flash",
            display_name="Gemini 2.0 Flash",
            max_tokens=1048576,
            supports_vision=True,
            supports_code=True,
            description="Fast and efficient with multimodal capabilities",
        ),
        ModelInfo(
            name="gemini-1.5-pro",
            display_name="Gemini 1.5 Pro",
            max_tokens=2097152,
            supports_vision=True,
            supports_code=True,
            description="Most capable model with largest context",
        ),
        ModelInfo(
            name="gemini-1.5-flash",
            display_name="Gemini 1.5 Flash",
            max_tokens=1048576,
            supports_vision=True,
            supports_code=True,
            description="Balanced speed and quality",
        ),
        ModelInfo(
            name="gemini-2.0-flash-lite",
            display_name="Gemini 2.0 Flash Lite",
            max_tokens=1048576,
            supports_vision=False,
            supports_code=True,
            description="Fastest model for simple tasks",
        ),
    ]

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        """
        Initialize Gemini provider.

        Args:
            model: Model to use. Defaults to GEMINI_MODEL env var or gemini-2.0-flash.
            api_key: API key. Defaults to GEMINI_API_KEY env var.

        Raises:
            APIKeyMissingError: If no API key is provided or found in environment.
        """
        logger.debug("Initializing Gemini provider", extra={"model": model})

        # Get API key
        self._api_key = api_key or os.getenv(GEMINI_API_KEY_ENV)
        if not self._api_key:
            logger.error("Gemini API key not found")
            raise APIKeyMissingError("Gemini", GEMINI_API_KEY_ENV)

        # Configure the genai library
        genai.configure(api_key=self._api_key)  # type: ignore[attr-defined]

        # Determine model from param, env, or default
        if model is None:
            model = os.getenv(GEMINI_MODEL_ENV, self.default_model)

        # Initialize parent (validates model)
        super().__init__(model=model)

        # Create the generative model instance
        self._client: genai.GenerativeModel | None = None  # type: ignore[name-defined]
        self._init_client()

        logger.debug(
            "Gemini provider initialized",
            extra={"model": self._model},
        )

    def _init_client(self) -> None:
        """Initialize or reinitialize the Gemini client."""
        self._client = genai.GenerativeModel(  # type: ignore[attr-defined]
            model_name=self._model,
            system_instruction=BLENDER_SYSTEM_PROMPT,
        )

    @property
    def model(self) -> str:
        """Return the currently selected model."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set the model, reinitializing the client."""
        logger.debug("Changing Gemini model", extra={"new_model": value})
        self._validate_model(value)
        self._model = value
        self._init_client()

    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.GEMINI

    @property
    def default_model(self) -> str:
        """Return the default model."""
        return "gemini-2.0-flash"

    @property
    def available_models(self) -> list[ModelInfo]:
        """Return list of available models."""
        return self.MODELS.copy()

    async def generate_code(
        self,
        user_request: str,
        context: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """
        Generate Blender Python code from natural language.

        Args:
            user_request: The user's natural language request.
            context: Optional context including scene info, history, etc.

        Returns:
            GenerationResult with the generated code and metadata.

        Raises:
            CodeGenerationError: If code generation fails.
            RateLimitError: If rate limit is exceeded.
            ProviderConnectionError: If connection fails.
        """
        logger.debug(
            "Generating code",
            extra={"request": user_request[:100], "model": self._model},
        )

        prompt = get_generation_prompt(user_request, context)

        try:
            response = await self._generate_content(prompt)
            raw_text = response.text
            code = extract_code_from_response(raw_text)

            # Extract token usage if available
            usage = getattr(response, "usage_metadata", None)
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            completion_tokens = getattr(usage, "candidates_token_count", None)
            total_tokens = getattr(usage, "total_token_count", None)

            logger.debug(
                "Code generated successfully",
                extra={
                    "code_length": len(code),
                    "total_tokens": total_tokens,
                },
            )

            return GenerationResult(
                code=code,
                model_used=self._model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                raw_response=raw_text,
            )

        except Exception as e:
            self._handle_api_error(e, "generate_code")
            raise  # Re-raise if not handled

    async def fix_code(
        self,
        code: str,
        error: str,
        original_request: str,
    ) -> FixResult:
        """
        Fix code that failed execution.

        Args:
            code: The code that failed.
            error: The error message.
            original_request: The original user request.

        Returns:
            FixResult with the fixed code and explanation.
        """
        logger.debug(
            "Fixing code",
            extra={"error": error[:100], "model": self._model},
        )

        prompt = get_fix_prompt(code, error, original_request)

        try:
            response = await self._generate_content(prompt)
            raw_text = response.text
            fixed_code = extract_code_from_response(raw_text)

            usage = getattr(response, "usage_metadata", None)
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            completion_tokens = getattr(usage, "candidates_token_count", None)

            logger.debug(
                "Code fixed",
                extra={"fixed_code_length": len(fixed_code)},
            )

            return FixResult(
                code=fixed_code,
                model_used=self._model,
                fix_explanation=None,  # Could parse from response
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        except Exception as e:
            self._handle_api_error(e, "fix_code")
            raise

    async def validate_connection(self) -> bool:
        """
        Validate that the Gemini connection is working.

        Returns:
            True if connection is valid.
        """
        logger.debug("Validating Gemini connection")
        try:
            # Simple test generation
            response = await self._generate_content("print('hello')")
            valid = response.text is not None
            logger.debug("Connection validation result", extra={"valid": valid})
            return valid
        except Exception as e:
            logger.warning(
                "Connection validation failed",
                extra={"error": str(e)},
            )
            return False

    async def _generate_content(self, prompt: str) -> Any:
        """Generate content using the Gemini model."""
        if self._client is None:
            raise ProviderConnectionError("Gemini", "Client not initialized")

        # Use generate_content_async for async operation
        return await self._client.generate_content_async(prompt)

    def _handle_api_error(self, error: Exception, operation: str) -> None:
        """Handle API errors and convert to appropriate exceptions."""
        error_str = str(error).lower()

        if "api key" in error_str or "invalid" in error_str:
            logger.error(
                f"API key error during {operation}", extra={"error": str(error)}
            )
            raise APIKeyInvalidError("Gemini", str(error)) from error

        if "rate limit" in error_str or "quota" in error_str:
            logger.warning(f"Rate limit hit during {operation}")
            raise RateLimitError("Gemini") from error

        if "connect" in error_str or "network" in error_str:
            logger.error(f"Connection error during {operation}")
            raise ProviderConnectionError("Gemini", str(error)) from error

        # Generic code generation error
        logger.error(
            f"Error during {operation}",
            extra={"error_type": type(error).__name__, "error": str(error)},
        )
        raise CodeGenerationError(f"Gemini {operation} failed: {error}") from error
