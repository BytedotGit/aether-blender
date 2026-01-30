"""
AI Module - Exceptions.

Custom exception hierarchy for AI provider errors.
"""


class AIProviderError(Exception):
    """Base exception for all AI provider errors."""

    pass


class APIKeyMissingError(AIProviderError):
    """API key not configured for the provider."""

    def __init__(self, provider_name: str, env_var: str) -> None:
        self.provider_name = provider_name
        self.env_var = env_var
        super().__init__(
            f"{provider_name} API key not found. "
            f"Set the {env_var} environment variable."
        )


class APIKeyInvalidError(AIProviderError):
    """API key is invalid or rejected by the provider."""

    def __init__(self, provider_name: str, message: str = "") -> None:
        self.provider_name = provider_name
        msg = f"{provider_name} API key is invalid."
        if message:
            msg += f" Details: {message}"
        super().__init__(msg)


class RateLimitError(AIProviderError):
    """API rate limit exceeded."""

    def __init__(self, provider_name: str, retry_after: float | None = None) -> None:
        self.provider_name = provider_name
        self.retry_after = retry_after
        msg = f"{provider_name} rate limit exceeded."
        if retry_after:
            msg += f" Retry after {retry_after} seconds."
        super().__init__(msg)


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

    def __init__(self, provider_name: str, message: str = "") -> None:
        self.provider_name = provider_name
        msg = f"Failed to connect to {provider_name}."
        if message:
            msg += f" Details: {message}"
        super().__init__(msg)
