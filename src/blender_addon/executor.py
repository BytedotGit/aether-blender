"""
Safe Code Executor for Aether Bridge.

This module provides safe code execution with stdout/stderr capture.
It is designed to execute arbitrary Python code inside Blender's
environment while capturing all output and handling errors gracefully.

CRITICAL: This code must ONLY be called from Blender's main thread.
The queue_handler ensures this by using bpy.app.timers.
"""

from __future__ import annotations

import contextlib
import logging
import math
import sys
import traceback
from io import StringIO
from typing import Any

# These imports are available in Blender's Python environment
try:
    import bpy
    import mathutils

    BLENDER_AVAILABLE = True
except ImportError:
    # Running outside Blender (e.g., for testing)
    BLENDER_AVAILABLE = False
    bpy = None  # type: ignore
    mathutils = None  # type: ignore

logger = logging.getLogger("aether_bridge.executor")

# Maximum output capture size (prevent memory exhaustion)
MAX_OUTPUT_SIZE = 1024 * 1024  # 1 MB


class ExecutionResult:
    """Result of code execution."""

    def __init__(
        self,
        success: bool,
        stdout: str = "",
        stderr: str = "",
        error: str | None = None,
        traceback_str: str | None = None,
        return_value: Any = None,
    ) -> None:
        """
        Initialize execution result.

        Args:
            success: Whether execution completed without error.
            stdout: Captured stdout output.
            stderr: Captured stderr output.
            error: Error message if execution failed.
            traceback_str: Full traceback if exception occurred.
            return_value: Return value from exec (typically None for exec).
        """
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.error = error
        self.traceback_str = traceback_str
        self.return_value = return_value

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        result = {
            "status": "success" if self.success else "error",
            "data": {},
            "logs": self.stdout,
        }
        if self.stderr:
            result["data"]["stderr"] = self.stderr
        if self.error:
            result["error"] = self.error
        if self.traceback_str:
            result["traceback"] = self.traceback_str
        if self.return_value is not None:
            with contextlib.suppress(Exception):
                # Attempt to serialize return value
                result["data"]["return_value"] = str(self.return_value)
        return result


def _create_execution_globals() -> dict[str, Any]:
    """
    Create the globals dictionary for code execution.

    Returns:
        Dictionary of available globals for executed code.
    """
    globals_dict: dict[str, Any] = {
        "__builtins__": __builtins__,
        "math": math,
    }

    if BLENDER_AVAILABLE:
        globals_dict["bpy"] = bpy
        globals_dict["mathutils"] = mathutils

    return globals_dict


def execute_code(code: str) -> ExecutionResult:
    """
    Execute Python code safely with output capture.

    Args:
        code: Python code string to execute.

    Returns:
        ExecutionResult with captured output and status.

    Note:
        This function MUST be called from Blender's main thread.
    """
    logger.debug("Executing code", extra={"code_length": len(code)})

    # Validate code is not empty
    if not code or not code.strip():
        logger.warning("Empty code received")
        return ExecutionResult(
            success=False,
            error="Empty code provided",
        )

    # Capture stdout/stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_stdout = StringIO()
    captured_stderr = StringIO()

    try:
        sys.stdout = captured_stdout
        sys.stderr = captured_stderr

        # Create execution environment
        exec_globals = _create_execution_globals()
        exec_locals: dict[str, Any] = {}

        # Execute the code
        exec(code, exec_globals, exec_locals)  # noqa: S102 - Expected behavior

        # Capture output
        stdout_output = captured_stdout.getvalue()
        stderr_output = captured_stderr.getvalue()

        # Truncate if too large
        if len(stdout_output) > MAX_OUTPUT_SIZE:
            stdout_output = stdout_output[:MAX_OUTPUT_SIZE] + "\n... (output truncated)"
        if len(stderr_output) > MAX_OUTPUT_SIZE:
            stderr_output = stderr_output[:MAX_OUTPUT_SIZE] + "\n... (output truncated)"

        logger.debug(
            "Code executed successfully",
            extra={
                "stdout_length": len(stdout_output),
                "stderr_length": len(stderr_output),
            },
        )

        return ExecutionResult(
            success=True,
            stdout=stdout_output,
            stderr=stderr_output,
        )

    except SyntaxError as e:
        logger.error(f"Syntax error in code: {e}")
        return ExecutionResult(
            success=False,
            stdout=captured_stdout.getvalue(),
            stderr=captured_stderr.getvalue(),
            error=f"SyntaxError: {e.msg} (line {e.lineno})",
            traceback_str=traceback.format_exc(),
        )

    except Exception as e:
        logger.error(f"Execution error: {e}")
        return ExecutionResult(
            success=False,
            stdout=captured_stdout.getvalue(),
            stderr=captured_stderr.getvalue(),
            error=f"{type(e).__name__}: {e}",
            traceback_str=traceback.format_exc(),
        )

    finally:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def validate_syntax(code: str) -> tuple[bool, str | None]:
    """
    Validate Python code syntax without executing.

    Args:
        code: Python code string to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    logger.debug("Validating syntax", extra={"code_length": len(code)})

    try:
        compile(code, "<aether>", "exec")
        return True, None
    except SyntaxError as e:
        error_msg = f"SyntaxError: {e.msg} (line {e.lineno})"
        logger.debug(f"Syntax validation failed: {error_msg}")
        return False, error_msg


def get_scene_info() -> dict[str, Any]:
    """
    Get basic scene information from Blender.

    Returns:
        Dictionary with scene information.

    Note:
        This function MUST be called from Blender's main thread.
    """
    if not BLENDER_AVAILABLE:
        return {"error": "Blender not available"}

    try:
        scene = bpy.context.scene  # type: ignore[union-attr]
        return {
            "name": scene.name,
            "frame_current": scene.frame_current,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "object_count": len(bpy.data.objects),  # type: ignore[union-attr]
            "objects": [obj.name for obj in bpy.data.objects[:100]],  # type: ignore[union-attr]
        }
    except Exception as e:
        logger.error(f"Failed to get scene info: {e}")
        return {"error": str(e)}


def get_object_list() -> list[dict[str, Any]]:
    """
    Get list of all objects in the scene.

    Returns:
        List of object information dictionaries.

    Note:
        This function MUST be called from Blender's main thread.
    """
    if not BLENDER_AVAILABLE:
        return []

    try:
        objects = []
        for obj in bpy.data.objects:  # type: ignore[union-attr]
            objects.append(
                {
                    "name": obj.name,
                    "type": obj.type,
                    "location": list(obj.location),  # type: ignore[arg-type]
                    "rotation": list(obj.rotation_euler),  # type: ignore[arg-type]
                    "scale": list(obj.scale),  # type: ignore[arg-type]
                }
            )
        return objects
    except Exception as e:
        logger.error(f"Failed to get object list: {e}")
        return []
