"""
Executor Module - __init__.py.

Safe execution of AI-generated code with retry logic and history tracking.
"""

from src.executor.exceptions import (
    ExecutionError,
    RetryExhaustedError,
    SyntaxValidationError,
    TimeoutError,
)
from src.executor.history import (
    ExecutionHistory,
    ExecutionRecord,
)
from src.executor.retry import (
    RetryConfig,
    RetryManager,
)
from src.executor.safe_exec import (
    ExecutionResult,
    SafeExecutor,
)

__all__ = [
    # Core
    "SafeExecutor",
    "ExecutionResult",
    # Retry
    "RetryConfig",
    "RetryManager",
    # History
    "ExecutionHistory",
    "ExecutionRecord",
    # Exceptions
    "ExecutionError",
    "SyntaxValidationError",
    "TimeoutError",
    "RetryExhaustedError",
]
