# AGENTS.md - Tests Module

## Purpose

Comprehensive test suite ensuring code quality and functionality.

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

## Test Template

```python
"""Tests for bridge.client module."""

import pytest
from unittest.mock import Mock, patch
from src.bridge.client import BlenderClient
from src.bridge.exceptions import ConnectionTimeoutError


class TestBlenderClientConnect:
    """Tests for BlenderClient.connect() method."""
    
    def test_connect_success_returns_true(self):
        """Test that connect() returns True on successful connection."""
        # Arrange
        client = BlenderClient(host="localhost", port=5005)
        
        # Act
        with patch.object(client, "_socket") as mock_socket:
            result = client.connect()
        
        # Assert
        assert result is True
        mock_socket.connect.assert_called_once()
    
    def test_connect_timeout_raises_exception(self):
        """Test that connect() raises ConnectionTimeoutError on timeout."""
        # Arrange
        client = BlenderClient(host="localhost", port=5005, timeout=0.1)
        
        # Act & Assert
        with pytest.raises(ConnectionTimeoutError):
            client.connect()
```

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
poetry run pytest tests/unit/bridge/

# Verbose with logs
poetry run pytest -v --log-cli-level=DEBUG

# Only unit tests
poetry run pytest tests/unit/

# Only integration tests
poetry run pytest tests/integration/

# Only e2e tests (requires Blender)
poetry run pytest tests/e2e/ -m e2e
```

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
