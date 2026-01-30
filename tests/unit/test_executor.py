"""
Unit Tests - Executor Module.

Tests for safe execution, retry logic, and execution history.
"""

import asyncio
from typing import Any

import pytest

from src.executor.exceptions import (
    RetryExhaustedError,
    SyntaxValidationError,
)
from src.executor.history import (
    ExecutionHistory,
    ExecutionStatus,
)
from src.executor.retry import RetryConfig, RetryManager
from src.executor.safe_exec import ExecutionResult, SafeExecutor


class TestSafeExecutorValidation:
    """Tests for syntax validation."""

    def test_validate_syntax_valid_code(self) -> None:
        """Test validation of valid Python code."""
        executor = SafeExecutor()
        is_valid, error, line = executor.validate_syntax("import bpy\nx = 1")

        assert is_valid is True
        assert error is None
        assert line is None

    def test_validate_syntax_invalid_code(self) -> None:
        """Test validation of invalid Python code."""
        executor = SafeExecutor()
        is_valid, error, line = executor.validate_syntax("def broken(")

        assert is_valid is False
        assert error is not None
        assert line is not None

    def test_detect_patterns_os_import(self) -> None:
        """Test detection of os import pattern."""
        executor = SafeExecutor()
        patterns = executor.detect_patterns("import os\nos.remove('file')")

        assert "os module import" in patterns

    def test_detect_patterns_file_open(self) -> None:
        """Test detection of file open pattern."""
        executor = SafeExecutor()
        patterns = executor.detect_patterns("f = open('file.txt')")

        assert "file open operation" in patterns

    def test_detect_patterns_no_matches(self) -> None:
        """Test when no patterns match."""
        executor = SafeExecutor()
        patterns = executor.detect_patterns(
            "import bpy\nbpy.ops.mesh.primitive_cube_add()"
        )

        assert len(patterns) == 0


class TestSafeExecutorPrepare:
    """Tests for code preparation."""

    def test_prepare_valid_code(self) -> None:
        """Test preparing valid code."""
        executor = SafeExecutor()
        code, warnings = executor.prepare_for_execution("import bpy")

        assert code == "import bpy"
        assert isinstance(warnings, list)

    def test_prepare_invalid_code_raises(self) -> None:
        """Test preparing invalid code raises error."""
        executor = SafeExecutor()

        with pytest.raises(SyntaxValidationError):
            executor.prepare_for_execution("def broken(")


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_create_from_response_success(self) -> None:
        """Test creating result from successful response."""
        executor = SafeExecutor()
        response = {
            "success": True,
            "stdout": "Hello",
            "stderr": "",
            "result": 42,
        }

        result = executor.create_result_from_response(
            code="print('Hello')",
            response=response,
            execution_time=0.1,
        )

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.stdout == "Hello"
        assert result.result == 42

    def test_create_from_response_failure(self) -> None:
        """Test creating result from failed response."""
        executor = SafeExecutor()
        response = {
            "success": False,
            "stdout": "",
            "stderr": "Error occurred",
            "error": {
                "message": "NameError: name 'x' is not defined",
                "type": "NameError",
                "line": 5,
            },
        }

        result = executor.create_result_from_response(
            code="print(x)",
            response=response,
        )

        assert result.success is False
        assert result.error_message == "NameError: name 'x' is not defined"
        assert result.error_type == "NameError"
        assert result.error_line == 5


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert abs(config.initial_delay - 0.5) < 0.001
        assert abs(config.max_delay - 10.0) < 0.001

    def test_get_delay_increases(self) -> None:
        """Test delay increases with attempts."""
        config = RetryConfig(initial_delay=1.0, jitter=False)

        delay1 = config.get_delay(1)
        delay2 = config.get_delay(2)
        delay3 = config.get_delay(3)

        assert delay1 < delay2 < delay3

    def test_get_delay_capped(self) -> None:
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            initial_delay=1.0,
            max_delay=5.0,
            exponential_base=10.0,
            jitter=False,
        )

        delay = config.get_delay(5)
        assert abs(delay - 5.0) < 0.001


class TestRetryManager:
    """Tests for retry manager."""

    @pytest.mark.asyncio
    async def test_execute_success_first_try(self) -> None:
        """Test execution succeeds on first try."""

        async def execute_fn(code: str) -> dict[str, Any]:
            await asyncio.sleep(0)  # Make it truly async
            return {"success": True, "result": "ok"}

        manager = RetryManager()
        result, attempts = await manager.execute_with_retry(
            execute_fn=execute_fn,
            code="test code",
        )

        assert result["success"] is True
        assert attempts == 1

    @pytest.mark.asyncio
    async def test_execute_retries_on_failure(self) -> None:
        """Test execution retries on failure."""
        attempt_counter = {"count": 0}

        async def execute_fn(code: str) -> dict[str, Any]:
            await asyncio.sleep(0)  # Make it truly async
            attempt_counter["count"] += 1
            if attempt_counter["count"] < 3:
                return {"success": False, "error": {"message": "Failed"}}
            return {"success": True}

        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        manager = RetryManager(config=config)

        result, attempts = await manager.execute_with_retry(
            execute_fn=execute_fn,
            code="test",
        )

        assert result["success"] is True
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_execute_exhausted_raises(self) -> None:
        """Test exhausted retries raises error."""

        async def execute_fn(code: str) -> dict[str, Any]:
            await asyncio.sleep(0)  # Make it truly async
            return {"success": False, "error": {"message": "Always fails"}}

        config = RetryConfig(max_attempts=2, initial_delay=0.01)
        manager = RetryManager(config=config)

        with pytest.raises(RetryExhaustedError) as exc_info:
            await manager.execute_with_retry(
                execute_fn=execute_fn,
                code="test",
            )

        assert exc_info.value.attempts == 2


class TestExecutionHistory:
    """Tests for execution history tracking."""

    def test_add_record(self) -> None:
        """Test adding execution record."""
        history = ExecutionHistory()

        record = history.add_record(
            user_request="create a cube",
            code="import bpy",
            status=ExecutionStatus.SUCCESS,
        )

        assert record.id.startswith("exec-")
        assert record.user_request == "create a cube"
        assert history.count == 1

    def test_get_recent(self) -> None:
        """Test getting recent records."""
        history = ExecutionHistory()

        for i in range(5):
            history.add_record(
                user_request=f"request {i}",
                code=f"code {i}",
                status=ExecutionStatus.SUCCESS,
            )

        recent = history.get_recent(3)
        assert len(recent) == 3
        # Should be newest first
        assert "request 4" in recent[0].user_request

    def test_get_failures(self) -> None:
        """Test getting failed records."""
        history = ExecutionHistory()

        history.add_record("req1", "code1", ExecutionStatus.SUCCESS)
        history.add_record(
            "req2", "code2", ExecutionStatus.FAILED, error_message="error"
        )
        history.add_record("req3", "code3", ExecutionStatus.SUCCESS)

        failures = history.get_failures()
        assert len(failures) == 1
        assert failures[0].user_request == "req2"

    def test_success_rate(self) -> None:
        """Test success rate calculation."""
        history = ExecutionHistory()

        history.add_record("r1", "c1", ExecutionStatus.SUCCESS)
        history.add_record("r2", "c2", ExecutionStatus.SUCCESS)
        history.add_record("r3", "c3", ExecutionStatus.FAILED)
        history.add_record("r4", "c4", ExecutionStatus.FIXED)

        # 3 successes (SUCCESS + SUCCESS + FIXED) out of 4
        assert history.success_rate == pytest.approx(0.75)

    def test_max_records_limit(self) -> None:
        """Test records are limited to max."""
        history = ExecutionHistory(max_records=5)

        for i in range(10):
            history.add_record(f"req{i}", f"code{i}", ExecutionStatus.SUCCESS)

        assert history.count == 5

    def test_clear(self) -> None:
        """Test clearing history."""
        history = ExecutionHistory()
        history.add_record("req", "code", ExecutionStatus.SUCCESS)
        history.add_record("req2", "code2", ExecutionStatus.SUCCESS)

        history.clear()

        assert history.count == 0

    def test_get_context_for_ai(self) -> None:
        """Test getting AI-formatted context."""
        history = ExecutionHistory()
        history.add_record("create cube", "import bpy", ExecutionStatus.SUCCESS)
        history.add_record(
            "fail request",
            "broken",
            ExecutionStatus.FAILED,
            error_message="SyntaxError",
        )

        context = history.get_context_for_ai()

        assert "history" in context
        assert "recent_successes" in context
        assert "recent_failures" in context
