"""
AI Module - Prompt Templates.

Helper functions for formatting context and error information
into prompts for the AI models.
"""

from typing import Any

from src.telemetry.logger import get_logger

logger = get_logger(__name__)

# Constants for code fence detection
CODE_FENCE_PYTHON = "```python"
CODE_FENCE = "```"
CODE_START_PATTERNS = ("import ", "from ", "def ", "class ", "#", "bpy.")


def _format_scene_objects(context: dict[str, Any]) -> str | None:
    """Format scene objects section."""
    objects = context.get("scene_objects")
    if not objects:
        return None
    obj_list = ", ".join(objects[:20])
    if len(objects) > 20:
        obj_list += f" ... and {len(objects) - 20} more"
    return f"**Scene Objects:** {obj_list}"


def _format_selected_objects(context: dict[str, Any]) -> str | None:
    """Format selected objects section."""
    selected = context.get("selected_objects")
    if not selected:
        return None
    return f"**Selected Objects:** {', '.join(selected)}"


def _format_active_object(context: dict[str, Any]) -> str | None:
    """Format active object section."""
    active = context.get("active_object")
    if not active:
        return None
    return f"**Active Object:** {active}"


def _format_animation_frames(context: dict[str, Any]) -> str | None:
    """Format animation frame information."""
    frame_info = []
    if "frame_current" in context:
        frame_info.append(f"Current: {context['frame_current']}")
    if "frame_start" in context:
        frame_info.append(f"Start: {context['frame_start']}")
    if "frame_end" in context:
        frame_info.append(f"End: {context['frame_end']}")
    if not frame_info:
        return None
    return f"**Animation Frames:** {', '.join(frame_info)}"


def _format_history(context: dict[str, Any]) -> str | None:
    """Format execution history section."""
    history = context.get("history")
    if not history:
        return None
    history_items = history[-5:]
    history_str = "\n".join(f"  - {item}" for item in history_items)
    return f"**Recent Commands:**\n{history_str}"


def format_context(context: dict[str, Any]) -> str:
    """
    Format context dictionary into a prompt-friendly string.

    Args:
        context: Dictionary containing context information.

    Returns:
        Formatted context string for inclusion in prompt.
    """
    logger.debug(
        "Formatting context",
        extra={"context_keys": list(context.keys()) if context else []},
    )
    if not context:
        return ""

    formatters = [
        _format_scene_objects,
        _format_selected_objects,
        _format_active_object,
        _format_animation_frames,
        _format_history,
    ]

    sections = [result for fmt in formatters if (result := fmt(context)) is not None]

    if not sections:
        return ""

    result = "## Current Context\n" + "\n".join(sections)
    logger.debug("Context formatted", extra={"sections_count": len(sections)})
    return result


def format_error_context(
    error_message: str,
    error_type: str | None = None,
    line_number: int | None = None,
    traceback: str | None = None,
) -> str:
    """
    Format error information for the fix prompt.

    Args:
        error_message: The error message.
        error_type: Type of error (e.g., "NameError", "TypeError").
        line_number: Line number where error occurred.
        traceback: Full traceback string.

    Returns:
        Formatted error context string.
    """
    sections = []

    if error_type:
        sections.append(f"**Error Type:** {error_type}")

    if line_number:
        sections.append(f"**Line:** {line_number}")

    sections.append(f"**Message:** {error_message}")

    if traceback:
        # Truncate long tracebacks
        tb_lines = traceback.strip().split("\n")
        if len(tb_lines) > 15:
            tb_lines = tb_lines[:5] + ["  ..."] + tb_lines[-10:]
        sections.append(f"**Traceback:**\n```\n{chr(10).join(tb_lines)}\n```")

    return "\n".join(sections)


def _extract_from_python_fence(response: str) -> str | None:
    """Extract code from ```python fence."""
    if CODE_FENCE_PYTHON not in response:
        return None
    start = response.find(CODE_FENCE_PYTHON) + len(CODE_FENCE_PYTHON)
    end = response.find(CODE_FENCE, start)
    if end > start:
        return response[start:end].strip()
    return None


def _extract_from_generic_fence(response: str) -> str | None:
    """Extract code from generic ``` fence."""
    if CODE_FENCE not in response:
        return None
    start = response.find(CODE_FENCE) + 3
    # Skip language identifier if present
    newline = response.find("\n", start)
    if newline > start:
        start = newline + 1
    end = response.find(CODE_FENCE, start)
    if end > start:
        return response[start:end].strip()
    return None


def _is_code_start(line: str) -> bool:
    """Check if a line looks like the start of Python code."""
    return line.startswith(CODE_START_PATTERNS)


def _is_non_code_line(line: str) -> bool:
    """Check if a line looks like explanatory text, not code."""
    non_code_prefixes = ("Note:", "This ", "The ", "I ", "Here")
    return line.startswith(non_code_prefixes) and not line.startswith("#")


def _extract_code_heuristically(response: str) -> str:
    """Extract code using heuristics when no fences present."""
    lines = response.split("\n")
    code_lines: list[str] = []
    in_code = False

    for line in lines:
        stripped = line.strip()
        if not in_code and _is_code_start(stripped):
            in_code = True
        if in_code:
            if _is_non_code_line(stripped):
                break
            code_lines.append(line)

    return "\n".join(code_lines).strip() if code_lines else response


def extract_code_from_response(response: str) -> str:
    """
    Extract Python code from an AI response.

    Handles responses that may include markdown code fences
    or explanatory text.

    Args:
        response: Raw response from AI model.

    Returns:
        Extracted Python code.
    """
    logger.debug(
        "Extracting code from response", extra={"response_length": len(response)}
    )
    response = response.strip()

    # Try extraction strategies in order
    result = _extract_from_python_fence(response)
    if result:
        logger.debug(
            "Extracted code from python fence", extra={"code_length": len(result)}
        )
        return result

    result = _extract_from_generic_fence(response)
    if result:
        logger.debug(
            "Extracted code from generic fence", extra={"code_length": len(result)}
        )
        return result

    result = _extract_code_heuristically(response)
    logger.debug("Extracted code heuristically", extra={"code_length": len(result)})
    return result
