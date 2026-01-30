"""
Executor Module - Exceptions.

Custom exception hierarchy for code execution errors.
"""


class ExecutionError(Exception):
    """Base exception for all execution errors."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stdout = stdout
        self.stderr = stderr


class SyntaxValidationError(ExecutionError):
    """Code failed syntax validation before execution."""

    def __init__(
        self,
        message: str,
        code: str,
        line_number: int | None = None,
        offset: int | None = None,
    ) -> None:
        super().__init__(message, code=code)
        self.line_number = line_number
        self.offset = offset


class TimeoutError(ExecutionError):
    """Code execution exceeded the allowed time limit."""

    def __init__(
        self,
        timeout_seconds: float,
        code: str | None = None,
    ) -> None:
        super().__init__(
            f"Execution timed out after {timeout_seconds} seconds",
            code=code,
        )
        self.timeout_seconds = timeout_seconds


class RetryExhaustedError(ExecutionError):
    """All retry attempts have been exhausted."""

    def __init__(
        self,
        attempts: int,
        last_error: str,
        code: str | None = None,
        errors: list[str] | None = None,
    ) -> None:
        super().__init__(
            f"All {attempts} retry attempts exhausted. Last error: {last_error}",
            code=code,
        )
        self.attempts = attempts
        self.last_error = last_error
        self.errors = errors or []
