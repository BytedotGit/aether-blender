"""
Executor Module - Execution History.

Tracks execution history for debugging, analytics, and context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.telemetry.logger import get_logger

logger = get_logger(__name__)


class ExecutionStatus(Enum):
    """Status of an execution."""

    SUCCESS = "success"
    FAILED = "failed"
    FIXED = "fixed"  # Failed initially but fixed on retry
    TIMEOUT = "timeout"
    SKIPPED = "skipped"  # Validation failed


@dataclass
class ExecutionRecord:
    """Record of a single execution attempt."""

    id: str
    timestamp: datetime
    user_request: str
    code: str
    status: ExecutionStatus
    model_used: str | None = None
    stdout: str = ""
    stderr: str = ""
    error_message: str | None = None
    error_type: str | None = None
    execution_time: float = 0.0
    attempts: int = 1
    fixes_applied: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


class ExecutionHistory:
    """
    Tracks execution history for the session.

    Provides context for AI to learn from past executions
    and avoid repeating mistakes.
    """

    def __init__(self, max_records: int = 100) -> None:
        """
        Initialize execution history.

        Args:
            max_records: Maximum records to keep in memory.
        """
        self._records: list[ExecutionRecord] = []
        self._max_records = max_records
        self._record_counter = 0
        logger.debug(
            "ExecutionHistory initialized",
            extra={"max_records": max_records},
        )

    def _generate_id(self) -> str:
        """Generate a unique ID for a record."""
        self._record_counter += 1
        return f"exec-{self._record_counter:04d}"

    def add_record(
        self,
        user_request: str,
        code: str,
        status: ExecutionStatus,
        model_used: str | None = None,
        stdout: str = "",
        stderr: str = "",
        error_message: str | None = None,
        error_type: str | None = None,
        execution_time: float = 0.0,
        attempts: int = 1,
        fixes_applied: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> ExecutionRecord:
        """
        Add a new execution record.

        Args:
            user_request: The original user request.
            code: The executed code.
            status: Execution status.
            model_used: AI model that generated the code.
            stdout: Standard output from execution.
            stderr: Standard error from execution.
            error_message: Error message if failed.
            error_type: Type of error if failed.
            execution_time: Execution duration in seconds.
            attempts: Number of attempts made.
            fixes_applied: List of fix descriptions if retried.
            context: Additional context data.

        Returns:
            The created ExecutionRecord.
        """
        record = ExecutionRecord(
            id=self._generate_id(),
            timestamp=datetime.now(),
            user_request=user_request,
            code=code,
            status=status,
            model_used=model_used,
            stdout=stdout,
            stderr=stderr,
            error_message=error_message,
            error_type=error_type,
            execution_time=execution_time,
            attempts=attempts,
            fixes_applied=fixes_applied or [],
            context=context or {},
        )

        self._records.append(record)

        # Trim if over limit
        if len(self._records) > self._max_records:
            removed = self._records.pop(0)
            logger.debug(
                "Removed old record to maintain limit",
                extra={"removed_id": removed.id},
            )

        logger.debug(
            "Execution record added",
            extra={
                "id": record.id,
                "status": record.status.value,
                "attempts": record.attempts,
            },
        )

        return record

    def get_recent(self, count: int = 10) -> list[ExecutionRecord]:
        """
        Get the most recent execution records.

        Args:
            count: Number of records to return.

        Returns:
            List of recent records (newest first).
        """
        return list(reversed(self._records[-count:]))

    def get_failures(self, count: int = 5) -> list[ExecutionRecord]:
        """
        Get recent failed executions.

        Useful for providing context to AI about what didn't work.

        Args:
            count: Maximum failures to return.

        Returns:
            List of failed records (newest first).
        """
        failures = [
            r
            for r in reversed(self._records)
            if r.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT)
        ]
        return failures[:count]

    def get_successes(self, count: int = 5) -> list[ExecutionRecord]:
        """
        Get recent successful executions.

        Useful for showing examples of working code.

        Args:
            count: Maximum successes to return.

        Returns:
            List of successful records (newest first).
        """
        successes = [
            r
            for r in reversed(self._records)
            if r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.FIXED)
        ]
        return successes[:count]

    def get_context_for_ai(self, max_examples: int = 3) -> dict[str, Any]:
        """
        Get execution history formatted for AI context.

        Args:
            max_examples: Maximum examples of each type.

        Returns:
            Dictionary with history context for AI prompts.
        """
        successes = self.get_successes(max_examples)
        failures = self.get_failures(max_examples)

        return {
            "history": [
                f"{r.user_request} → {'✓' if r.status.value.startswith('success') else '✗'}"
                for r in self.get_recent(5)
            ],
            "recent_successes": [
                {"request": r.user_request, "code_snippet": r.code[:200]}
                for r in successes
            ],
            "recent_failures": [
                {"request": r.user_request, "error": r.error_message} for r in failures
            ],
        }

    def clear(self) -> None:
        """Clear all execution records."""
        count = len(self._records)
        self._records.clear()
        logger.info("Execution history cleared", extra={"records_removed": count})

    @property
    def count(self) -> int:
        """Return the number of records in history."""
        return len(self._records)

    @property
    def success_rate(self) -> float:
        """Calculate success rate of executions."""
        if not self._records:
            return 0.0
        successes = sum(
            1
            for r in self._records
            if r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.FIXED)
        )
        return successes / len(self._records)
