"""
Blender Setup Script for Aether-Blender.

Downloads and configures Blender 4.2 LTS for the project.
This script is idempotent - safe to run multiple times.

Usage:
    python scripts/setup_blender.py [--verify] [--force]

Options:
    --verify  Launch Blender to verify installation works
    --force   Re-download even if already present
"""

import argparse
import hashlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError

# Add src to path for logging
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.telemetry.logger import get_logger

    logger = get_logger(__name__)
except ImportError:
    # Fallback if logging not available
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)


# Configuration
BLENDER_VERSION = "4.2.0"
BLENDER_URL = (
    f"https://download.blender.org/release/Blender4.2/"
    f"blender-{BLENDER_VERSION}-windows-x64.zip"
)
BLENDER_SHA256 = ""  # Will be populated when we know the actual hash

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
INSTALL_PATH = TOOLS_DIR / "blender"
DOWNLOAD_PATH = TOOLS_DIR / f"blender-{BLENDER_VERSION}-windows-x64.zip"
EXECUTABLE = INSTALL_PATH / "blender.exe"


def is_installed() -> bool:
    """Check if Blender is already installed and executable exists."""
    return EXECUTABLE.exists()


def download_blender(force: bool = False) -> Path:
    """
    Download Blender ZIP file.

    Args:
        force: If True, re-download even if file exists

    Returns:
        Path to downloaded ZIP file
    """
    if DOWNLOAD_PATH.exists() and not force:
        logger.info(
            "Blender ZIP already downloaded", extra={"path": str(DOWNLOAD_PATH)}
        )
        return DOWNLOAD_PATH

    logger.info("Starting Blender download", extra={"url": BLENDER_URL})
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        _perform_download()
        return DOWNLOAD_PATH
    except HTTPError as e:
        logger.error(f"HTTP Error: {e.code} {e.reason}", extra={"url": BLENDER_URL})
        raise
    except URLError as e:
        logger.error(f"URL Error: {e.reason}", extra={"url": BLENDER_URL})
        raise
    except Exception as e:
        logger.error("Download failed", extra={"error": str(e)})
        raise


def _perform_download() -> None:
    """Perform the actual download with progress logging."""
    request = urllib.request.Request(
        BLENDER_URL,
        headers={
            "User-Agent": "Aether-Blender/1.0 (https://github.com/BytedotGit/aether-blender)"
        },
    )
    with urllib.request.urlopen(request) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        block_size = 8192
        last_logged_percent = -10

        with open(DOWNLOAD_PATH, "wb") as out_file:
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)

                if total_size > 0:
                    percent = int((downloaded / total_size) * 100)
                    # Log every 10%
                    if percent >= last_logged_percent + 10:
                        last_logged_percent = (percent // 10) * 10
                        mb_dl = downloaded / 1024 / 1024
                        mb_tot = total_size / 1024 / 1024
                        logger.info(
                            f"Download: {last_logged_percent}% ({mb_dl:.0f}/{mb_tot:.0f} MB)"
                        )

    logger.info(
        "Download complete",
        extra={"size_mb": f"{DOWNLOAD_PATH.stat().st_size / 1024 / 1024:.1f}"},
    )


def verify_checksum(zip_path: Path) -> bool:
    """
    Verify the downloaded file's SHA256 checksum.

    Args:
        zip_path: Path to the ZIP file

    Returns:
        True if checksum matches or no checksum configured
    """
    if not BLENDER_SHA256:
        logger.warning("No checksum configured, skipping verification")
        return True

    logger.info("Verifying checksum")
    sha256_hash = hashlib.sha256()

    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)

    actual_hash = sha256_hash.hexdigest()
    if actual_hash != BLENDER_SHA256:
        logger.error(
            "Checksum mismatch",
            extra={"expected": BLENDER_SHA256, "actual": actual_hash},
        )
        return False

    logger.info("Checksum verified")
    return True


def extract_blender(zip_path: Path, force: bool = False) -> None:
    """
    Extract Blender to installation path.

    Args:
        zip_path: Path to the ZIP file
        force: If True, re-extract even if already extracted
    """
    if INSTALL_PATH.exists() and not force:
        logger.info("Blender already extracted", extra={"path": str(INSTALL_PATH)})
        return

    if INSTALL_PATH.exists() and force:
        logger.info("Removing existing installation for re-extraction")
        shutil.rmtree(INSTALL_PATH)

    logger.info("Extracting Blender", extra={"destination": str(INSTALL_PATH)})
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    # Extract to temp location first
    temp_extract = TOOLS_DIR / "blender_temp"
    if temp_extract.exists():
        shutil.rmtree(temp_extract)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_extract)

    # Find the extracted folder (usually named blender-X.X.X-windows-x64)
    extracted_folders = list(temp_extract.iterdir())
    if len(extracted_folders) == 1 and extracted_folders[0].is_dir():
        # Move the inner folder to the final location
        shutil.move(str(extracted_folders[0]), str(INSTALL_PATH))
        shutil.rmtree(temp_extract)
    else:
        # Move the temp folder itself
        shutil.move(str(temp_extract), str(INSTALL_PATH))

    logger.info("Extraction complete")


def verify_installation() -> bool:
    """
    Verify Blender can launch and report its version.

    Returns:
        True if Blender launches successfully
    """
    if not EXECUTABLE.exists():
        logger.error("Blender executable not found", extra={"path": str(EXECUTABLE)})
        return False

    logger.info("Verifying Blender installation")

    try:
        result = subprocess.run(
            [str(EXECUTABLE), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.error(
                "Blender returned non-zero exit code",
                extra={"code": result.returncode, "stderr": result.stderr},
            )
            return False

        if f"Blender {BLENDER_VERSION[:3]}" in result.stdout:
            logger.info(
                "Blender verification successful",
                extra={"version": result.stdout.strip().split("\n")[0]},
            )
            return True
        else:
            logger.warning(
                "Unexpected Blender version",
                extra={"output": result.stdout.strip()},
            )
            return True  # Still consider it a success

    except subprocess.TimeoutExpired:
        logger.error("Blender verification timed out")
        return False
    except Exception as e:
        logger.error("Blender verification failed", extra={"error": str(e)})
        return False


def setup_blender(force: bool = False, verify: bool = False) -> bool:
    """
    Main setup function.

    Args:
        force: Force re-download and re-extraction
        verify: Launch Blender to verify installation

    Returns:
        True if setup completed successfully
    """
    logger.info(
        "Starting Blender setup",
        extra={"version": BLENDER_VERSION, "force": force, "verify": verify},
    )

    # Check if already installed
    if is_installed() and not force:
        logger.info("Blender already installed")
        if verify:
            return verify_installation()
        return True

    try:
        # Download
        zip_path = download_blender(force=force)

        # Verify checksum
        if not verify_checksum(zip_path):
            return False

        # Extract
        extract_blender(zip_path, force=force)

        # Verify
        if not verify_installation():
            return False

        logger.info("Blender setup completed successfully")
        return True

    except Exception as e:
        logger.error("Blender setup failed", extra={"error": str(e)})
        return False


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Setup Blender for Aether-Blender project"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Launch Blender to verify installation",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download and re-extraction",
    )
    args = parser.parse_args()

    success = setup_blender(force=args.force, verify=args.verify)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
