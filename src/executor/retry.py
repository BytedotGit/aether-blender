"""
Executor Module - Retry Logic.

Exponential backoff retry mechanism for failed code execution.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from src.executor.exceptions import RetryExhaustedError
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# Constant for unknown error messages
UNKNOWN_ERROR = "Unknown error"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    initial_delay: float = 0.5
    max_delay: float = 10.0
    exponential_base: float = 2.0
    jitter: bool = True

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.

        Args:
            attempt: The attempt number (1-indexed).

        Returns:
            Delay in seconds.
        """
        import random

        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add up to 25% random jitter
            jitter = delay * 0.25 * random.random()
            delay += jitter

        return delay


class RetryManager:
    """
    Manages retry logic for code execution.

    Works with AI providers to fix code on failure and retry.
    """

    def __init__(self, config: RetryConfig | None = None) -> None:
        """
        Initialize retry manager.

        Args:
            config: Retry configuration. Uses defaults if None.
        """
        self._config = config or RetryConfig()
        logger.debug(
            "RetryManager initialized",
            extra={
                "max_attempts": self._config.max_attempts,
                "initial_delay": self._config.initial_delay,
            },
        )

    @property
    def config(self) -> RetryConfig:
        """Return the retry configuration."""
        return self._config

    async def execute_with_retry(
        self,
        execute_fn: Callable[[str], Any],
        fix_fn: Callable[[str, str], str] | None = None,
        code: str = "",
        _context: dict[str, Any] | None = None,
    ) -> tuple[Any, int]:
        """
        Execute code with automatic retry on failure.

        Args:
            execute_fn: Async function that executes code and returns result.
            fix_fn: Optional async function to fix code. Takes (code, error) -> fixed_code.
            code: Initial code to execute.
            _context: Optional context for the fix function (reserved for future use).

        Returns:
            Tuple of (result, attempts_used).

        Raises:
            RetryExhaustedError: If all attempts fail.
        """
        errors: list[str] = []
        current_code = code

        for attempt in range(1, self._config.max_attempts + 1):
            logger.debug(
                f"Execution attempt {attempt}/{self._config.max_attempts}",
                extra={"attempt": attempt, "code_length": len(current_code)},
            )

            try:
                result = await execute_fn(current_code)

                # Check if result indicates success
                if self._is_success(result):
                    logger.info(
                        "Execution succeeded",
                        extra={"attempt": attempt, "total_attempts": attempt},
                    )
                    return result, attempt

                # Extract error from result
                error_msg = self._extract_error(result)
                errors.append(error_msg)

                logger.warning(
                    f"Execution failed on attempt {attempt}",
                    extra={"error": error_msg},
                )

            except Exception as e:
                error_msg = str(e)
                errors.append(error_msg)
                logger.warning(
                    f"Exception on attempt {attempt}",
                    extra={"error": error_msg, "type": type(e).__name__},
                )

            # If we have more attempts and a fix function, try to fix the code
            if attempt < self._config.max_attempts and fix_fn is not None:
                try:
                    delay = self._config.get_delay(attempt)
                    logger.debug(f"Waiting {delay:.2f}s before retry")
                    await asyncio.sleep(delay)

                    logger.debug("Attempting to fix code")
                    current_code = await fix_fn(current_code, error_msg)
                    logger.debug(
                        "Code fixed",
                        extra={"new_code_length": len(current_code)},
                    )
                except Exception as fix_error:
                    logger.warning(
                        "Failed to fix code",
                        extra={"error": str(fix_error)},
                    )

            elif attempt < self._config.max_attempts:
                # No fix function, just wait and retry same code
                delay = self._config.get_delay(attempt)
                logger.debug(f"Waiting {delay:.2f}s before retry (no fix)")
                await asyncio.sleep(delay)

        # All attempts exhausted
        logger.error(
            "All retry attempts exhausted",
            extra={"attempts": self._config.max_attempts, "errors": errors},
        )
        raise RetryExhaustedError(
            attempts=self._config.max_attempts,
            last_error=errors[-1] if errors else UNKNOWN_ERROR,
            code=current_code,
            errors=errors,
        )

    def _is_success(self, result: Any) -> bool:
        """Check if execution result indicates success."""
        if isinstance(result, dict):
            return result.get("success", False)
        if hasattr(result, "success"):
            return result.success
        return True  # Assume success if no clear indicator

    def _extract_error(self, result: Any) -> str:
        """Extract error message from failed result."""
        if isinstance(result, dict):
            error = result.get("error", {})
            if isinstance(error, dict):
                return error.get("message", str(error))
            return str(error) if error else UNKNOWN_ERROR
        if hasattr(result, "error_message"):
            return result.error_message or UNKNOWN_ERROR
        return str(result)
