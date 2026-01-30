"""
Executor Module - Safe Execution.

Wrapper for executing AI-generated Python code with stdout/stderr capture.
This module prepares code for execution via the Bridge client.
"""

import ast
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.telemetry.logger import get_logger

logger = get_logger(__name__)

# Patterns that should be logged (not blocked, just tracked)
LOGGED_PATTERNS = [
    (r"\bimport\s+os\b", "os module import"),
    (r"\bimport\s+subprocess\b", "subprocess module import"),
    (r"\bimport\s+shutil\b", "shutil module import"),
    (r"\bopen\s*\(", "file open operation"),
    (r"\b__import__\s*\(", "dynamic import"),
    (r"\beval\s*\(", "eval call"),
    (r"\bexec\s*\(", "exec call"),
]


@dataclass
class ExecutionResult:
    """Result from code execution."""

    success: bool
    code: str
    stdout: str = ""
    stderr: str = ""
    result: Any = None
    error_message: str | None = None
    error_type: str | None = None
    error_line: int | None = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class SafeExecutor:
    """
    Safe code executor with validation and logging.

    This class validates and prepares code for execution.
    Actual execution happens via the Bridge client in Blender.
    """

    def __init__(self, log_patterns: bool = True) -> None:
        """
        Initialize the safe executor.

        Args:
            log_patterns: Whether to log detected patterns.
        """
        logger.debug("Initializing SafeExecutor", extra={"log_patterns": log_patterns})
        self._log_patterns = log_patterns

    def validate_syntax(self, code: str) -> tuple[bool, str | None, int | None]:
        """
        Validate Python syntax of the code.

        Args:
            code: The Python code to validate.

        Returns:
            Tuple of (is_valid, error_message, error_line).
        """
        logger.debug("Validating syntax", extra={"code_length": len(code)})

        try:
            ast.parse(code)
            logger.debug("Syntax validation passed")
            return True, None, None
        except SyntaxError as e:
            error_msg = f"{e.msg} at line {e.lineno}"
            logger.warning(
                "Syntax validation failed",
                extra={"error": error_msg, "line": e.lineno},
            )
            return False, error_msg, e.lineno

    def detect_patterns(self, code: str) -> list[str]:
        """
        Detect patterns that should be logged for awareness.

        Args:
            code: The Python code to check.

        Returns:
            List of detected pattern descriptions.
        """
        detected = []
        for pattern, description in LOGGED_PATTERNS:
            if re.search(pattern, code):
                detected.append(description)

        if detected and self._log_patterns:
            logger.info(
                "Patterns detected in code",
                extra={"patterns": detected},
            )

        return detected

    def prepare_for_execution(self, code: str) -> tuple[str, list[str]]:
        """
        Prepare code for execution.

        Validates syntax and wraps code for stdout/stderr capture.

        Args:
            code: The Python code to prepare.

        Returns:
            Tuple of (prepared_code, warnings).

        Raises:
            SyntaxValidationError: If syntax is invalid.
        """
        from src.executor.exceptions import SyntaxValidationError

        logger.debug("Preparing code for execution", extra={"code_length": len(code)})

        # Validate syntax
        is_valid, error_msg, error_line = self.validate_syntax(code)
        if not is_valid:
            raise SyntaxValidationError(
                message=error_msg or "Syntax error",
                code=code,
                line_number=error_line,
            )

        # Detect patterns for logging
        warnings = self.detect_patterns(code)

        # Code is ready - actual execution happens via Bridge
        logger.debug("Code prepared for execution", extra={"warnings": warnings})

        return code, warnings

    def create_result_from_response(
        self,
        code: str,
        response: dict[str, Any],
        execution_time: float = 0.0,
        warnings: list[str] | None = None,
    ) -> ExecutionResult:
        """
        Create an ExecutionResult from a Bridge response.

        Args:
            code: The executed code.
            response: The response from the Bridge client.
            execution_time: Time taken to execute.
            warnings: Any warnings from preparation.

        Returns:
            ExecutionResult object.
        """
        success = response.get("success", False)
        error = response.get("error")

        return ExecutionResult(
            success=success,
            code=code,
            stdout=response.get("stdout", ""),
            stderr=response.get("stderr", ""),
            result=response.get("result"),
            error_message=error.get("message") if error else None,
            error_type=error.get("type") if error else None,
            error_line=error.get("line") if error else None,
            execution_time=execution_time,
            warnings=warnings or [],
            metadata={"response": response},
        )
