"""
AI Module - Prompts Package.

System prompts and templates for Blender code generation.
"""

from src.ai.prompts.system import (
    BLENDER_SYSTEM_PROMPT,
    CODE_FIX_PROMPT,
    get_fix_prompt,
    get_generation_prompt,
)
from src.ai.prompts.templates import (
    format_context,
    format_error_context,
)

__all__ = [
    "BLENDER_SYSTEM_PROMPT",
    "CODE_FIX_PROMPT",
    "get_generation_prompt",
    "get_fix_prompt",
    "format_context",
    "format_error_context",
]
