"""
AI Module - Exceptions.

Custom exception hierarchy for AI provider errors.
"""


class AIProviderError(Exception):
    """Base exception for all AI provider errors."""

    pass


class APIKeyMissingError(AIProviderError):
    """API key not configured for the provider."""

    def __init__(self, message: str = "", env_var: str | None = None) -> None:
        """
        Initialize APIKeyMissingError.

        Args:
            message: Error message or provider name.
            env_var: Optional environment variable name.
        """
        self.env_var = env_var
        if env_var:
            full_msg = f"{message} Set the {env_var} environment variable."
        else:
            full_msg = message
        super().__init__(full_msg)


class APIKeyInvalidError(AIProviderError):
    """API key is invalid or rejected by the provider."""

    def __init__(self, message: str = "") -> None:
        """
        Initialize APIKeyInvalidError.

        Args:
            message: Error message describing the issue.
        """
        super().__init__(message or "API key is invalid.")


class RateLimitError(AIProviderError):
    """API rate limit exceeded."""

    def __init__(self, message: str = "", retry_after: float | None = None) -> None:
        """
        Initialize RateLimitError.

        Args:
            message: Error message or provider name.
            retry_after: Optional seconds until retry is allowed.
        """
        self.retry_after = retry_after
        if retry_after and message:
            full_msg = f"{message} Retry after {retry_after} seconds."
        elif retry_after:
            full_msg = f"Rate limit exceeded. Retry after {retry_after} seconds."
        else:
            full_msg = message or "Rate limit exceeded."
        super().__init__(full_msg)


class ModelUnavailableError(AIProviderError):
    """Requested model is not available."""

    def __init__(
        self, model_name: str, available_models: list[str] | None = None
    ) -> None:
        self.model_name = model_name
        self.available_models = available_models or []
        msg = f"Model '{model_name}' is not available."
        if self.available_models:
            msg += f" Available models: {', '.join(self.available_models)}"
        super().__init__(msg)


class CodeGenerationError(AIProviderError):
    """Failed to generate valid code from the AI provider."""

    def __init__(self, message: str, raw_response: str | None = None) -> None:
        self.raw_response = raw_response
        super().__init__(message)


class ContextTooLongError(AIProviderError):
    """Input context exceeds the model's maximum token limit."""

    def __init__(self, max_tokens: int, current_tokens: int | None = None) -> None:
        self.max_tokens = max_tokens
        self.current_tokens = current_tokens
        msg = f"Context exceeds maximum of {max_tokens} tokens."
        if current_tokens:
            msg += f" Current: {current_tokens} tokens."
        super().__init__(msg)


class ProviderConnectionError(AIProviderError):
    """Failed to connect to the AI provider."""

    def __init__(self, message: str = "") -> None:
        """
        Initialize ProviderConnectionError.

        Args:
            message: Error message describing the connection failure.
        """
        super().__init__(message or "Failed to connect to AI provider.")


class ProviderNotFoundError(AIProviderError):
    """Requested provider is not available or not registered."""

    def __init__(self, provider_name: str, available: list[str] | None = None) -> None:
        self.provider_name = provider_name
        self.available = available or []
        msg = f"Provider '{provider_name}' not found."
        if self.available:
            msg += f" Available providers: {', '.join(self.available)}"
        super().__init__(msg)
