#!/usr/bin/env python3
"""
Check that logging is used in source files.

Pre-commit hook that verifies:
1. Logger is imported from src.telemetry.logger
2. Logger is instantiated with get_logger(__name__)
3. Logger is actually used (debug/info/warning/error calls)
"""

import re
import sys
from pathlib import Path


def check_logging(filepath: str) -> tuple[bool, str]:
    """
    Check if a file has proper logging.

    Args:
        filepath: Path to the Python file

    Returns:
        Tuple of (passed, message)
    """
    path = Path(filepath)

    if not path.exists():
        return True, ""

    if not filepath.endswith(".py"):
        return True, ""

    # Skip __init__.py files
    if path.name == "__init__.py":
        return True, ""

    # Skip test files
    if "test" in path.name.lower():
        return True, ""

    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return True, ""

    # Check for logger import
    import_pattern = r"from src\.telemetry\.logger import.*get_logger"
    has_import = bool(re.search(import_pattern, content))

    # Check for logger instantiation
    has_instantiation = "get_logger(__name__)" in content

    # Check for logging calls
    log_patterns = [
        r"logger\.debug\(",
        r"logger\.info\(",
        r"logger\.warning\(",
        r"logger\.error\(",
        r"logger\.critical\(",
    ]
    has_logging_calls = any(re.search(p, content) for p in log_patterns)

    # For files with actual code (not just imports/empty)
    # Check if file has functions
    has_functions = "def " in content

    if not has_functions:
        return True, ""  # No functions, no logging needed

    issues = []
    if not has_import:
        issues.append("Missing: from src.telemetry.logger import get_logger")
    if not has_instantiation:
        issues.append("Missing: logger = get_logger(__name__)")
    if not has_logging_calls:
        issues.append("No logging calls found (logger.debug/info/etc)")

    if issues:
        return False, f"{filepath}: {'; '.join(issues)}"

    return True, ""


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        return 0

    failed = False
    for filepath in sys.argv[1:]:
        passed, message = check_logging(filepath)
        if not passed:
            print(message)
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
