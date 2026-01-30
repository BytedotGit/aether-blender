"""
Orchestrator Module - Exceptions.

Custom exception hierarchy for orchestration errors.
"""


class OrchestratorError(Exception):
    """Base exception for all orchestrator errors."""

    pass


class PipelineError(OrchestratorError):
    """Error during pipeline execution."""

    def __init__(self, message: str, stage: str | None = None) -> None:
        """
        Initialize PipelineError.

        Args:
            message: Error message.
            stage: Optional pipeline stage where error occurred.
        """
        self.stage = stage
        if stage:
            message = f"[{stage}] {message}"
        super().__init__(message)


class BlenderNotConnectedError(OrchestratorError):
    """Blender is not connected or available."""

    def __init__(self, message: str = "Blender is not connected") -> None:
        super().__init__(message)


class ExecutionFailedError(OrchestratorError):
    """Code execution failed after all retry attempts."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        attempts: int = 0,
    ) -> None:
        """
        Initialize ExecutionFailedError.

        Args:
            message: Error message.
            code: The code that failed.
            attempts: Number of attempts made.
        """
        self.code = code
        self.attempts = attempts
        super().__init__(message)
