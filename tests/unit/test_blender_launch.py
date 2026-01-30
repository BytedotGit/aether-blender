"""
Blender Launch Verification Tests.

These tests verify that the Blender executable is properly installed
and can be launched successfully. This is a Phase 1 requirement to
ensure the development environment is complete.
"""

import subprocess
from pathlib import Path

import pytest

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
BLENDER_PATH = PROJECT_ROOT / "tools" / "blender" / "blender.exe"


class TestBlenderInstallation:
    """Tests verifying Blender is installed correctly."""

    def test_blender_executable_exists(self) -> None:
        """Test that the Blender executable file exists."""
        assert BLENDER_PATH.exists(), (
            f"Blender executable not found at {BLENDER_PATH}. "
            "Run 'poetry run python scripts/setup_blender.py' to install."
        )

    def test_blender_executable_is_file(self) -> None:
        """Test that Blender path points to a file, not directory."""
        if not BLENDER_PATH.exists():
            pytest.skip("Blender not installed")

        assert BLENDER_PATH.is_file(), f"{BLENDER_PATH} is not a file"

    def test_blender_directory_structure(self) -> None:
        """Test that Blender directory has expected structure."""
        if not BLENDER_PATH.exists():
            pytest.skip("Blender not installed")

        blender_dir = BLENDER_PATH.parent

        # Check for expected directories/files
        expected_paths = [
            blender_dir / "4.2",
            blender_dir / "4.2" / "python",
            blender_dir / "4.2" / "scripts",
        ]

        for expected in expected_paths:
            assert expected.exists(), f"Expected path missing: {expected}"


class TestBlenderLaunch:
    """Tests verifying Blender can be launched."""

    @pytest.mark.skipif(
        not BLENDER_PATH.exists(),
        reason="Blender not installed",
    )
    def test_blender_version_command(self) -> None:
        """Test that Blender responds to --version command."""
        result = subprocess.run(
            [str(BLENDER_PATH), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Blender failed: {result.stderr}"
        assert "Blender" in result.stdout, "Version output doesn't contain 'Blender'"
        assert "4.2" in result.stdout, "Expected Blender 4.2.x"

    @pytest.mark.skipif(
        not BLENDER_PATH.exists(),
        reason="Blender not installed",
    )
    def test_blender_python_version(self) -> None:
        """Test that Blender's embedded Python works."""
        # Run a simple Python expression in Blender
        python_code = "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')"

        result = subprocess.run(
            [
                str(BLENDER_PATH),
                "--background",
                "--python-expr",
                python_code,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Blender Python failed: {result.stderr}"
        assert (
            "Python 3.11" in result.stdout
        ), f"Expected Python 3.11, got: {result.stdout}"

    @pytest.mark.skipif(
        not BLENDER_PATH.exists(),
        reason="Blender not installed",
    )
    def test_blender_background_mode(self) -> None:
        """Test that Blender runs in background (headless) mode."""
        result = subprocess.run(
            [
                str(BLENDER_PATH),
                "--background",
                "--python-expr",
                "print('Background mode works')",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Background mode failed: {result.stderr}"
        assert "Background mode works" in result.stdout

    @pytest.mark.skipif(
        not BLENDER_PATH.exists(),
        reason="Blender not installed",
    )
    def test_blender_bpy_import(self) -> None:
        """Test that bpy module can be imported in Blender."""
        python_code = """
import bpy
print(f'Blender version: {bpy.app.version_string}')
print(f'Scene name: {bpy.context.scene.name}')
"""
        result = subprocess.run(
            [
                str(BLENDER_PATH),
                "--background",
                "--python-expr",
                python_code,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"bpy import failed: {result.stderr}"
        assert "Blender version:" in result.stdout
        assert "Scene name:" in result.stdout


class TestBlenderPythonEnvironment:
    """Tests verifying Blender's Python environment."""

    @pytest.mark.skipif(
        not BLENDER_PATH.exists(),
        reason="Blender not installed",
    )
    def test_blender_can_import_json(self) -> None:
        """Test that json module works in Blender Python."""
        python_code = """
import json
data = {'test': True, 'value': 42}
result = json.dumps(data)
print(f'JSON: {result}')
"""
        result = subprocess.run(
            [
                str(BLENDER_PATH),
                "--background",
                "--python-expr",
                python_code,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0
        assert '"test": true' in result.stdout or '"test":true' in result.stdout

    @pytest.mark.skipif(
        not BLENDER_PATH.exists(),
        reason="Blender not installed",
    )
    def test_blender_can_import_socket(self) -> None:
        """Test that socket module works in Blender Python (needed for bridge)."""
        python_code = """
import socket
print(f'Socket module available: {socket.AF_INET}')
"""
        result = subprocess.run(
            [
                str(BLENDER_PATH),
                "--background",
                "--python-expr",
                python_code,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0
        assert "Socket module available:" in result.stdout

    @pytest.mark.skipif(
        not BLENDER_PATH.exists(),
        reason="Blender not installed",
    )
    def test_blender_can_import_threading(self) -> None:
        """Test that threading module works in Blender Python (needed for server)."""
        python_code = """
import threading
print(f'Threading available: {threading.current_thread().name}')
"""
        result = subprocess.run(
            [
                str(BLENDER_PATH),
                "--background",
                "--python-expr",
                python_code,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0
        assert "Threading available:" in result.stdout
