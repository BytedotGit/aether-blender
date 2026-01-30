# AGENTS.md - Tests Module

## Purpose

Comprehensive test suite ensuring code quality and functionality.

---

## MANDATORY: Tests for Every Feature

### The Iron Rule

**NO source code is complete without corresponding tests.**

For every file in `src/`, there MUST be a corresponding test file in `tests/`.

### File Mapping

| Source File | Test File |
|-------------|-----------|
| `src/bridge/client.py` | `tests/unit/test_bridge_client.py` |
| `src/ai/provider.py` | `tests/unit/test_ai_provider.py` |
| `src/gui/chat_window.py` | `tests/unit/test_gui_chat_window.py` |

### Test Creation Checklist

When writing tests, cover:

```text
□ Happy path - Normal expected usage
□ Edge cases - Empty inputs, boundary values, max values
□ Error cases - Invalid inputs, missing dependencies
□ Exception handling - Verify correct exceptions raised
□ Logging verification - Check logging calls (optional but recommended)
```

---

## Structure

```text
tests/
├── unit/           # Fast, isolated tests (mock external deps)
├── integration/    # Tests involving multiple components
├── e2e/            # End-to-end tests (requires Blender)
├── fixtures/       # Shared test data and fixtures
├── conftest.py     # Pytest configuration and shared fixtures
└── AGENTS.md       # THIS FILE
```

## Naming Convention

```text
test_<module>_<function>_<scenario>_<expected>.py
```

Example:

```text
test_bridge_client_connect_success.py
test_bridge_client_connect_timeout_raises_exception.py
```

---

## Test Template

```python
"""Tests for <module>.<file> module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.module.file import SomeClass, some_function


class TestSomeFunctionHappyPath:
    """Tests for some_function() - happy path scenarios."""

    def test_some_function_valid_input_returns_expected(self):
        """Test that some_function returns expected result for valid input."""
        # Arrange
        input_value = "valid_input"
        expected = "expected_output"

        # Act
        result = some_function(input_value)

        # Assert
        assert result == expected

    def test_some_function_with_options_applies_options(self):
        """Test that some_function applies optional parameters."""
        # Arrange / Act / Assert
        pass


class TestSomeFunctionEdgeCases:
    """Tests for some_function() - edge cases."""

    def test_some_function_empty_string_returns_empty(self):
        """Test that some_function handles empty string gracefully."""
        result = some_function("")
        assert result == ""

    def test_some_function_max_length_handles_boundary(self):
        """Test that some_function handles maximum length input."""
        long_input = "x" * 10000
        result = some_function(long_input)
        assert len(result) <= 10000


class TestSomeFunctionErrors:
    """Tests for some_function() - error scenarios."""

    def test_some_function_none_input_raises_typeerror(self):
        """Test that some_function raises TypeError for None input."""
        with pytest.raises(TypeError, match="must be str"):
            some_function(None)

    def test_some_function_invalid_type_raises_typeerror(self):
        """Test that some_function raises TypeError for wrong type."""
        with pytest.raises(TypeError):
            some_function(123)


class TestSomeFunctionLogging:
    """Tests for some_function() - verify logging behavior."""

    def test_some_function_logs_entry_and_exit(self):
        """Test that some_function logs entry and exit."""
        with patch("src.module.file.logger") as mock_logger:
            some_function("test")

            # Verify logging occurred
            assert mock_logger.debug.call_count >= 2
```

---

## Fixtures Location

Shared fixtures go in `conftest.py`:

```python
# tests/conftest.py
import pytest

@pytest.fixture
def mock_blender_client():
    """Provide a mock Blender client for testing."""
    from unittest.mock import Mock
    client = Mock()
    client.connected = True
    return client

@pytest.fixture
def sample_code():
    """Provide sample Blender code for testing."""
    return "import bpy; bpy.ops.mesh.primitive_cube_add()"

@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing logging behavior."""
    from unittest.mock import MagicMock
    return MagicMock()
```

## Coverage Requirements

| Module       | Minimum Coverage |
| ------------ | ---------------- |
| Overall      | 80%              |
| bridge       | 95%              |
| executor     | 95%              |
| ai           | 80%              |
| gui          | 60%              |
| orchestrator | 80%              |
| project      | 80%              |
| export       | 80%              |

## Running Tests

```powershell
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=src --cov-report=html

# Specific module
poetry run pytest tests/unit/test_bridge_client.py

# Verbose with logs
poetry run pytest -v --log-cli-level=DEBUG

# Only unit tests
poetry run pytest tests/unit/

# Only integration tests
poetry run pytest tests/integration/

# Only e2e tests (requires Blender)
poetry run pytest tests/e2e/ -m e2e

# Show which tests exist
poetry run pytest --collect-only
```

---

## E2E Test Requirements

End-to-end tests that require Blender:

1. Must be marked with `@pytest.mark.e2e`
2. Must skip gracefully if Blender not available
3. Must clean up Blender state after test

```python
import pytest

@pytest.mark.e2e
def test_create_cube_in_blender():
    """Test that we can create a cube in Blender."""
    if not blender_available():
        pytest.skip("Blender not available")

    # Test logic here
    pass
```

## Test Data

Store test data in `tests/fixtures/`:

```text
tests/fixtures/
├── sample_project.aether
├── test_scene.blend
├── sample_code/
│   ├── valid_cube.py
│   └── invalid_syntax.py
└── expected_outputs/
    └── cube_created.json
```

## Mocking Blender

Since `bpy` is only available inside Blender, use `fake-bpy-module`:

```python
# For type hints and basic mocking
from unittest.mock import MagicMock
import sys

# Mock bpy for unit tests
sys.modules['bpy'] = MagicMock()
```

---

## Validation Before Commit

```bash
# Verify all tests pass
poetry run pytest -v

# Check coverage
poetry run pytest --cov=src --cov-report=term-missing

# Verify test file exists for source file
python scripts/validate_feature.py src/your_file.py
```

---

## Recent Tests Added

| Date       | Test File | Coverage | Author |
| ---------- | --------- | -------- | ------ |
| 2026-01-30 | test_sanity.py | 100% | Agent |
