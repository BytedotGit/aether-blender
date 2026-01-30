"""
Sanity Tests for Aether-Blender.

These tests verify the basic project setup and environment.
They should always pass if the project is correctly configured.
"""

import sys
from pathlib import Path


class TestProjectStructure:
    """Tests for project directory structure."""

    def test_src_directory_exists(self, project_root: Path):
        """Test that src directory exists."""
        assert (project_root / "src").is_dir()

    def test_tests_directory_exists(self, project_root: Path):
        """Test that tests directory exists."""
        assert (project_root / "tests").is_dir()

    def test_scripts_directory_exists(self, project_root: Path):
        """Test that scripts directory exists."""
        assert (project_root / "scripts").is_dir()

    def test_agents_md_exists(self, project_root: Path):
        """Test that root AGENTS.md exists."""
        assert (project_root / "AGENTS.md").is_file()

    def test_roadmap_exists(self, project_root: Path):
        """Test that ROADMAP.md exists."""
        assert (project_root / "ROADMAP.md").is_file()

    def test_pyproject_exists(self, project_root: Path):
        """Test that pyproject.toml exists."""
        assert (project_root / "pyproject.toml").is_file()


class TestModuleStructure:
    """Tests for module directories."""

    def test_telemetry_module_exists(self, project_root: Path):
        """Test that telemetry module exists."""
        assert (project_root / "src" / "telemetry").is_dir()

    def test_bridge_module_exists(self, project_root: Path):
        """Test that bridge module exists."""
        assert (project_root / "src" / "bridge").is_dir()

    def test_ai_module_exists(self, project_root: Path):
        """Test that AI module exists."""
        assert (project_root / "src" / "ai").is_dir()

    def test_gui_module_exists(self, project_root: Path):
        """Test that GUI module exists."""
        assert (project_root / "src" / "gui").is_dir()


class TestLoggingSystem:
    """Tests for the logging system."""

    def test_logger_module_exists(self, project_root: Path):
        """Test that logger module exists."""
        assert (project_root / "src" / "telemetry" / "logger.py").is_file()

    def test_can_import_logger(self):
        """Test that logger can be imported."""
        from src.telemetry.logger import get_logger

        logger = get_logger("test")
        assert logger is not None

    def test_logger_has_correct_name(self):
        """Test that logger has the correct name."""
        from src.telemetry.logger import get_logger

        logger = get_logger("test.module")
        assert logger.name == "test.module"


class TestPythonEnvironment:
    """Tests for Python environment."""

    def test_python_version(self):
        """Test that Python version is 3.11+."""
        assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"

    def test_can_import_pathlib(self):
        """Test that pathlib is available."""
        from pathlib import Path

        assert Path is not None

    def test_can_import_json(self):
        """Test that json is available."""
        import json

        assert json is not None


class TestSanity:
    """Basic sanity checks."""

    def test_true_is_true(self):
        """The most basic test - ensures pytest works."""
        assert True

    def test_one_plus_one(self):
        """Basic arithmetic test."""
        assert 1 + 1 == 2

    def test_string_operations(self):
        """Basic string test."""
        assert "aether".upper() == "AETHER"
