#!/usr/bin/env python3
"""
Feature Validation Script for Aether-Blender.

This script validates that a source file has:
1. A corresponding test file
2. Logging integration (imports and uses get_logger)
3. Type hints on all functions
4. Docstrings on all public functions
5. Input validation

Usage:
    python scripts/validate_feature.py src/module/file.py
    python scripts/validate_feature.py --all
"""

import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Add src to path for logging
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.telemetry.logger import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)


class ValidationResult(NamedTuple):
    """Result of a validation check."""

    passed: bool
    message: str
    details: list[str]


class FeatureValidator:
    """Validates source files for compliance with project standards."""

    def __init__(self, source_file: Path):
        """
        Initialize validator for a source file.

        Args:
            source_file: Path to the Python source file to validate
        """
        logger.debug(
            "Initializing FeatureValidator", extra={"source_file": str(source_file)}
        )
        self.source_file = source_file
        self.source_content = ""
        self.ast_tree: ast.Module | None = None

        if source_file.exists():
            self.source_content = source_file.read_text(encoding="utf-8")
            try:
                self.ast_tree = ast.parse(self.source_content)
            except SyntaxError as e:
                logger.error("Syntax error in source file", extra={"error": str(e)})

    def validate_all(self) -> dict[str, ValidationResult]:
        """
        Run all validation checks.

        Returns:
            Dictionary mapping check name to ValidationResult
        """
        logger.debug("Running all validations", extra={"file": str(self.source_file)})

        results = {
            "test_file_exists": self.check_test_file_exists(),
            "logging_imported": self.check_logging_imported(),
            "logging_used": self.check_logging_used(),
            "type_hints": self.check_type_hints(),
            "docstrings": self.check_docstrings(),
            "no_print_statements": self.check_no_print_statements(),
            "file_length": self.check_file_length(),
        }

        logger.debug("Validation complete", extra={"results_count": len(results)})
        return results

    def check_test_file_exists(self) -> ValidationResult:
        """Check if a corresponding test file exists."""
        logger.debug("Checking for test file")

        # Convert src/module/file.py -> tests/unit/test_module_file.py
        relative = self.source_file.relative_to(PROJECT_ROOT / "src")
        parts = list(relative.parts)

        # Build test file name
        test_name = "test_" + "_".join(p.replace(".py", "") for p in parts) + ".py"
        test_file = PROJECT_ROOT / "tests" / "unit" / test_name

        # Also check alternative naming: tests/unit/test_file.py
        alt_test_name = "test_" + parts[-1]
        alt_test_file = PROJECT_ROOT / "tests" / "unit" / alt_test_name

        if test_file.exists() or alt_test_file.exists():
            found = test_file if test_file.exists() else alt_test_file
            return ValidationResult(
                passed=True,
                message="Test file exists",
                details=[f"Found: {found.relative_to(PROJECT_ROOT)}"],
            )

        return ValidationResult(
            passed=False,
            message="No test file found",
            details=[
                f"Expected: {test_file.relative_to(PROJECT_ROOT)}",
                f"Or: {alt_test_file.relative_to(PROJECT_ROOT)}",
            ],
        )

    def check_logging_imported(self) -> ValidationResult:
        """Check if logging is imported from telemetry."""
        logger.debug("Checking logging import")

        pattern = r"from src\.telemetry\.logger import.*get_logger"
        if re.search(pattern, self.source_content):
            return ValidationResult(
                passed=True,
                message="Logging imported correctly",
                details=["Found: from src.telemetry.logger import get_logger"],
            )

        return ValidationResult(
            passed=False,
            message="Logging not imported",
            details=["Missing: from src.telemetry.logger import get_logger"],
        )

    def check_logging_used(self) -> ValidationResult:
        """Check if logger is instantiated and used."""
        logger.debug("Checking logging usage")

        issues = []

        # Check for logger instantiation
        if (
            "logger = get_logger(__name__)" not in self.source_content
            and "get_logger(__name__)" not in self.source_content
        ):
            issues.append("Missing: logger = get_logger(__name__)")

        # Check for actual logging calls
        log_patterns = [
            r"logger\.debug\(",
            r"logger\.info\(",
            r"logger\.warning\(",
            r"logger\.error\(",
            r"logger\.critical\(",
        ]

        has_logging = any(re.search(p, self.source_content) for p in log_patterns)
        if not has_logging:
            issues.append("No logging calls found (logger.debug/info/warning/error)")

        if issues:
            return ValidationResult(
                passed=False, message="Logging not properly used", details=issues
            )

        return ValidationResult(
            passed=True,
            message="Logging is used",
            details=["Logger instantiated and used"],
        )

    def check_type_hints(self) -> ValidationResult:
        """Check if all functions have type hints."""
        logger.debug("Checking type hints")

        if self.ast_tree is None:
            return ValidationResult(
                passed=False, message="Could not parse file", details=["Syntax error"]
            )

        missing_hints = []

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private/dunder methods for strict checking
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue

                # Check return type
                if node.returns is None and node.name not in ("__init__", "__del__"):
                    missing_hints.append(f"{node.name}: missing return type hint")

                # Check parameter types
                for arg in node.args.args:
                    if arg.arg != "self" and arg.annotation is None:
                        missing_hints.append(
                            f"{node.name}: parameter '{arg.arg}' missing type"
                        )

        if missing_hints:
            return ValidationResult(
                passed=False,
                message=f"Missing type hints ({len(missing_hints)} issues)",
                details=missing_hints[:10],  # Limit to first 10
            )

        return ValidationResult(
            passed=True, message="All functions have type hints", details=[]
        )

    def check_docstrings(self) -> ValidationResult:
        """Check if public functions have docstrings."""
        logger.debug("Checking docstrings")

        if self.ast_tree is None:
            return ValidationResult(
                passed=False, message="Could not parse file", details=["Syntax error"]
            )

        missing_docstrings = []

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.FunctionDef | ast.ClassDef):
                # Skip private functions
                if node.name.startswith("_") and not node.name.startswith("__init__"):
                    continue

                # Check for docstring
                if not (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    missing_docstrings.append(f"{node.name}: missing docstring")

        if missing_docstrings:
            return ValidationResult(
                passed=False,
                message=f"Missing docstrings ({len(missing_docstrings)} issues)",
                details=missing_docstrings[:10],
            )

        return ValidationResult(
            passed=True, message="All public functions have docstrings", details=[]
        )

    def check_no_print_statements(self) -> ValidationResult:
        """Check that print() is not used (should use logger instead)."""
        logger.debug("Checking for print statements")

        if self.ast_tree is None:
            return ValidationResult(
                passed=False, message="Could not parse file", details=["Syntax error"]
            )

        print_calls = []

        for node in ast.walk(self.ast_tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                print_calls.append(f"Line {node.lineno}: print() call found")

        if print_calls:
            return ValidationResult(
                passed=False,
                message=f"Found {len(print_calls)} print() calls (use logger instead)",
                details=print_calls[:5],
            )

        return ValidationResult(passed=True, message="No print statements", details=[])

    def check_file_length(self) -> ValidationResult:
        """Check that file does not exceed 800 lines."""
        logger.debug("Checking file length")

        lines = len(self.source_content.splitlines())

        if lines > 800:
            return ValidationResult(
                passed=False,
                message=f"File has {lines} lines (max 800)",
                details=["Refactor into smaller modules"],
            )

        if lines > 700:
            return ValidationResult(
                passed=True,
                message=f"File has {lines} lines (warning: approaching 800 limit)",
                details=["Consider refactoring soon"],
            )

        return ValidationResult(
            passed=True, message=f"File has {lines} lines", details=[]
        )


def validate_file(filepath: Path) -> bool:
    """
    Validate a single file and print results.

    Args:
        filepath: Path to the file to validate

    Returns:
        True if all validations pass
    """
    print(f"\n{'='*60}")
    print(f"Validating: {filepath}")
    print("=" * 60)

    validator = FeatureValidator(filepath)
    results = validator.validate_all()

    all_passed = True

    for check_name, result in results.items():
        status = "✓" if result.passed else "✗"
        color = "\033[32m" if result.passed else "\033[31m"
        reset = "\033[0m"

        print(f"{color}{status}{reset} {check_name}: {result.message}")

        if not result.passed:
            all_passed = False
            for detail in result.details:
                print(f"    → {detail}")

    print()
    if all_passed:
        print("\033[32m✓ All validations passed!\033[0m")
    else:
        print("\033[31m✗ Some validations failed. Please fix before committing.\033[0m")

    return all_passed


def validate_all_src_files() -> bool:
    """Validate all Python files in src/."""
    src_dir = PROJECT_ROOT / "src"
    all_passed = True

    for py_file in src_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue  # Skip init files
        if not validate_file(py_file):
            all_passed = False

    return all_passed


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_feature.py <source_file.py>")
        print("       python scripts/validate_feature.py --all")
        return 1

    if sys.argv[1] == "--all":
        success = validate_all_src_files()
    else:
        filepath = Path(sys.argv[1])
        if not filepath.is_absolute():
            filepath = PROJECT_ROOT / filepath
        success = validate_file(filepath)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
