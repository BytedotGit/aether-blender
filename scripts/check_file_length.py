#!/usr/bin/env python3
"""
Check file length for pre-commit hook.

Ensures no Python file exceeds 800 lines per AGENTS.md guidelines.
"""

import sys
from pathlib import Path

MAX_LINES = 800
WARNING_THRESHOLD = 700


def check_file(filepath: str) -> tuple[bool, str]:
    """
    Check if a file exceeds the line limit.

    Args:
        filepath: Path to the file to check

    Returns:
        Tuple of (passed, message)
    """
    path = Path(filepath)
    if not path.exists():
        return True, ""

    if not filepath.endswith(".py"):
        return True, ""

    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            lines = len(f.readlines())
    except Exception as e:
        return True, f"Warning: Could not read {filepath}: {e}"

    if lines > MAX_LINES:
        return False, f"ERROR: {filepath} has {lines} lines (max {MAX_LINES})"
    elif lines > WARNING_THRESHOLD:
        return (
            True,
            f"WARNING: {filepath} has {lines} lines (approaching {MAX_LINES} limit)",
        )

    return True, ""


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        return 0

    failed = False
    for filepath in sys.argv[1:]:
        passed, message = check_file(filepath)
        if message:
            print(message)
        if not passed:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
