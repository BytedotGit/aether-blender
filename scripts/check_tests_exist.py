#!/usr/bin/env python3
"""
Check that test files exist for source files.

Pre-commit hook that verifies every source file in src/
has a corresponding test file in tests/unit/.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def check_tests_exist(filepath: str) -> tuple[bool, str]:
    """
    Check if a test file exists for a source file.

    Args:
        filepath: Path to the Python source file

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

    # Only check src/ files
    try:
        relative = path.relative_to(PROJECT_ROOT / "src")
    except ValueError:
        return True, ""  # Not in src/

    # Build expected test file paths
    parts = list(relative.parts)

    # Primary: tests/unit/test_module_file.py
    test_name = "test_" + "_".join(p.replace(".py", "") for p in parts) + ".py"
    test_file = PROJECT_ROOT / "tests" / "unit" / test_name

    # Alternative: tests/unit/test_file.py
    alt_test_name = "test_" + parts[-1]
    alt_test_file = PROJECT_ROOT / "tests" / "unit" / alt_test_name

    # Alternative: tests/unit/module/test_file.py
    if len(parts) > 1:
        subdir_test = PROJECT_ROOT / "tests" / "unit" / parts[0] / ("test_" + parts[-1])
    else:
        subdir_test = None

    if test_file.exists():
        return True, ""
    if alt_test_file.exists():
        return True, ""
    if subdir_test and subdir_test.exists():
        return True, ""

    return False, (
        f"WARNING: {filepath} has no test file.\n"
        f"  Expected: tests/unit/{test_name}\n"
        f"  Or: tests/unit/{alt_test_name}"
    )


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        return 0

    warnings = []
    for filepath in sys.argv[1:]:
        passed, message = check_tests_exist(filepath)
        if not passed:
            warnings.append(message)

    # Print warnings but don't fail the commit
    # (to allow WIP commits - but the warning is visible)
    for warning in warnings:
        print(warning)

    # Return 0 to not block commits, just warn
    # Change to `return 1 if warnings else 0` to enforce
    return 0


if __name__ == "__main__":
    sys.exit(main())
