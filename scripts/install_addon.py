#!/usr/bin/env python3
"""Install Aether Bridge addon into Blender's addons directory.

This script creates a symlink (or copies) the addon source to Blender's
addons folder, enabling it to be loaded via addon_utils.enable().

Usage:
    poetry run python scripts/install_addon.py [--copy] [--uninstall]

Options:
    --copy      Copy files instead of symlink (use on systems without symlink support)
    --uninstall Remove the addon from Blender's addons directory
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from src.telemetry.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

# Constants
ADDON_NAME = "aether_bridge"
ADDON_SOURCE = PROJECT_ROOT / "src" / "blender_addon"
BLENDER_DIR = PROJECT_ROOT / "tools" / "blender"
BLENDER_VERSION = "4.2"
ADDONS_TARGET = BLENDER_DIR / BLENDER_VERSION / "scripts" / "addons" / ADDON_NAME


def find_blender_addons_dir() -> Path | None:
    """Find the Blender addons directory.

    Returns:
        Path to Blender's addons directory, or None if not found.
    """
    logger.debug("Searching for Blender addons directory")

    # Check standard location for portable installation
    if ADDONS_TARGET.parent.exists():
        logger.debug(
            "Found addons directory",
            extra={"path": str(ADDONS_TARGET.parent)},
        )
        return ADDONS_TARGET.parent

    # Try to find other Blender versions
    if BLENDER_DIR.exists():
        for version_dir in BLENDER_DIR.iterdir():
            if version_dir.is_dir() and version_dir.name[0].isdigit():
                addons_dir = version_dir / "scripts" / "addons"
                if addons_dir.exists():
                    logger.debug(
                        "Found addons directory for version",
                        extra={
                            "version": version_dir.name,
                            "path": str(addons_dir),
                        },
                    )
                    return addons_dir

    logger.warning("Blender addons directory not found")
    return None


def install_symlink() -> bool:
    """Install addon via symlink.

    Returns:
        True if installation succeeded, False otherwise.
    """
    logger.info(
        "Installing addon via symlink",
        extra={
            "source": str(ADDON_SOURCE),
            "target": str(ADDONS_TARGET),
        },
    )

    if not ADDON_SOURCE.exists():
        logger.error(
            "Addon source directory does not exist",
            extra={"path": str(ADDON_SOURCE)},
        )
        return False

    # Ensure parent directory exists
    ADDONS_TARGET.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing if present
    if ADDONS_TARGET.exists() or ADDONS_TARGET.is_symlink():
        logger.debug(
            "Removing existing addon installation",
            extra={"path": str(ADDONS_TARGET)},
        )
        if ADDONS_TARGET.is_symlink() or ADDONS_TARGET.is_file():
            ADDONS_TARGET.unlink()
        else:
            shutil.rmtree(ADDONS_TARGET)

    # Create symlink
    try:
        ADDONS_TARGET.symlink_to(ADDON_SOURCE, target_is_directory=True)
        logger.info(
            "Symlink created successfully",
            extra={
                "link": str(ADDONS_TARGET),
                "target": str(ADDON_SOURCE),
            },
        )
        return True
    except OSError as err:
        logger.error(
            "Failed to create symlink (try running as administrator or use --copy)",
            extra={"error": str(err)},
        )
        return False


def install_copy() -> bool:
    """Install addon via file copy.

    Returns:
        True if installation succeeded, False otherwise.
    """
    logger.info(
        "Installing addon via copy",
        extra={
            "source": str(ADDON_SOURCE),
            "target": str(ADDONS_TARGET),
        },
    )

    if not ADDON_SOURCE.exists():
        logger.error(
            "Addon source directory does not exist",
            extra={"path": str(ADDON_SOURCE)},
        )
        return False

    # Ensure parent directory exists
    ADDONS_TARGET.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing if present
    if ADDONS_TARGET.exists():
        logger.debug(
            "Removing existing addon installation",
            extra={"path": str(ADDONS_TARGET)},
        )
        shutil.rmtree(ADDONS_TARGET)

    # Copy files
    try:
        shutil.copytree(
            ADDON_SOURCE,
            ADDONS_TARGET,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"),
        )
        logger.info(
            "Files copied successfully",
            extra={"target": str(ADDONS_TARGET)},
        )
        return True
    except OSError as err:
        logger.error(
            "Failed to copy addon files",
            extra={"error": str(err)},
        )
        return False


def uninstall() -> bool:
    """Remove addon from Blender's addons directory.

    Returns:
        True if uninstallation succeeded, False otherwise.
    """
    logger.info(
        "Uninstalling addon",
        extra={"path": str(ADDONS_TARGET)},
    )

    if not ADDONS_TARGET.exists() and not ADDONS_TARGET.is_symlink():
        logger.warning(
            "Addon not installed",
            extra={"path": str(ADDONS_TARGET)},
        )
        return True

    try:
        if ADDONS_TARGET.is_symlink():
            ADDONS_TARGET.unlink()
        else:
            shutil.rmtree(ADDONS_TARGET)
        logger.info("Addon uninstalled successfully")
        return True
    except OSError as err:
        logger.error(
            "Failed to uninstall addon",
            extra={"error": str(err)},
        )
        return False


def verify_installation() -> bool:
    """Verify the addon installation.

    Returns:
        True if addon is properly installed, False otherwise.
    """
    logger.debug("Verifying addon installation")

    if not ADDONS_TARGET.exists():
        logger.error("Addon directory does not exist")
        return False

    # Check for required files
    init_file = ADDONS_TARGET / "__init__.py"
    if not init_file.exists():
        logger.error("Addon __init__.py not found")
        return False

    # Check for bl_info
    content = init_file.read_text()
    if "bl_info" not in content:
        logger.error("Addon __init__.py missing bl_info")
        return False

    # Check for other required modules
    required_modules = ["server.py", "executor.py", "queue_handler.py"]
    for module in required_modules:
        if not (ADDONS_TARGET / module).exists():
            logger.error(
                "Required module missing",
                extra={"module": module},
            )
            return False

    logger.info(
        "Addon installation verified",
        extra={
            "path": str(ADDONS_TARGET),
            "is_symlink": ADDONS_TARGET.is_symlink(),
        },
    )
    return True


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Install Aether Bridge addon into Blender"
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of creating symlink",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall the addon",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify installation only",
    )
    args = parser.parse_args()

    logger.info("Aether Bridge addon installer starting")

    # Find Blender addons directory
    addons_dir = find_blender_addons_dir()
    if addons_dir is None and not args.verify:
        logger.error("Could not find Blender addons directory")
        logger.info(
            "Ensure Blender is installed at",
            extra={"path": str(BLENDER_DIR)},
        )
        return 1

    # Handle verify-only mode
    if args.verify:
        return 0 if verify_installation() else 1

    # Handle uninstall
    if args.uninstall:
        return 0 if uninstall() else 1

    # Install addon
    success = install_copy() if args.copy else install_symlink()

    if not success:
        return 1

    # Verify installation
    if not verify_installation():
        logger.error("Installation verification failed")
        return 1

    logger.info("Addon installation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
