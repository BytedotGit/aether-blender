"""
Pytest Configuration and Shared Fixtures.

This module contains fixtures available to all tests.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Mock bpy for unit tests (bpy is only available inside Blender)
# ============================================================================
@pytest.fixture(autouse=True)
def mock_bpy():
    """Mock bpy module for tests that don't run inside Blender."""
    mock = MagicMock()
    sys.modules["bpy"] = mock
    yield mock
    if "bpy" in sys.modules:
        del sys.modules["bpy"]


# ============================================================================
# Project Path Fixtures
# ============================================================================
@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def logs_dir(project_root: Path) -> Path:
    """Return the logs directory, creating it if needed."""
    logs = project_root / "logs"
    logs.mkdir(exist_ok=True)
    return logs


@pytest.fixture
def tools_dir(project_root: Path) -> Path:
    """Return the tools directory."""
    return project_root / "tools"


# ============================================================================
# Sample Data Fixtures
# ============================================================================
@pytest.fixture
def sample_blender_code() -> str:
    """Return sample valid Blender Python code."""
    return """
import bpy

# Create a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"
"""


@pytest.fixture
def sample_invalid_code() -> str:
    """Return sample invalid Python code for error testing."""
    return "def broken("  # Syntax error


@pytest.fixture
def sample_json_rpc_request() -> dict:
    """Return a sample JSON-RPC request."""
    return {
        "jsonrpc": "2.0",
        "id": "test-123",
        "method": "execute_code",
        "params": {
            "code": "import bpy; bpy.ops.mesh.primitive_cube_add()",
            "timeout": 5000,
        },
    }


@pytest.fixture
def sample_json_rpc_response() -> dict:
    """Return a sample JSON-RPC response."""
    return {
        "jsonrpc": "2.0",
        "id": "test-123",
        "result": {
            "status": "success",
            "data": {"object_name": "Cube"},
            "logs": "",
            "error": None,
        },
    }


# ============================================================================
# Mock Client Fixtures
# ============================================================================
@pytest.fixture
def mock_blender_client():
    """Provide a mock Blender client for testing."""
    client = MagicMock()
    client.connected = True
    client.host = "localhost"
    client.port = 5005
    return client


# ============================================================================
# Mock AI Provider Fixtures
# ============================================================================
@pytest.fixture
def mock_gemini_provider():
    """Provide a mock Gemini AI provider for testing."""
    # Create mock ModelInfo objects with .name attribute
    mock_model_1 = MagicMock()
    mock_model_1.name = "gemini-1.5-flash"
    mock_model_2 = MagicMock()
    mock_model_2.name = "gemini-1.5-pro"

    provider = MagicMock()
    provider.name = "gemini"
    provider.current_model = "gemini-1.5-flash"
    provider.available_models = [mock_model_1, mock_model_2]
    return provider


# ============================================================================
# Test Markers
# ============================================================================
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "e2e: marks tests as end-to-end (requires Blender)",
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow running",
    )
