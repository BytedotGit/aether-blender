# AGENTS.md - Scripts Module

## Purpose

Automation scripts for development environment setup and maintenance.

## Files

| File                   | Purpose                              |
| ---------------------- | ------------------------------------ |
| `setup_blender.py`     | Download and configure Blender 4.2   |
| `install_addon.py`     | Install Aether addon into Blender    |
| `run_blender_tests.py` | Execute tests inside Blender         |

## setup_blender.py Requirements

### Functionality

1. Check if Blender already installed in `tools/blender/`
2. If not, download Blender 4.2 LTS portable ZIP
3. Extract to `tools/blender/`
4. Verify executable exists
5. Optionally launch to verify functionality

### Idempotency

Script must be safe to run multiple times:

- Skip download if already present
- Skip extraction if already extracted
- Always verify final state

### Implementation Pattern

```python
"""
Blender Setup Script

Downloads and configures Blender 4.2 LTS for Aether-Blender.

Usage:
    python scripts/setup_blender.py [--verify] [--force]

Options:
    --verify  Launch Blender to verify installation
    --force   Re-download even if already present
"""

import argparse
import urllib.request
import zipfile
import subprocess
from pathlib import Path

BLENDER_VERSION = "4.2.0"
BLENDER_URL = "https://download.blender.org/release/Blender4.2/blender-4.2.0-windows-x64.zip"
INSTALL_PATH = Path("tools/blender")
EXECUTABLE = INSTALL_PATH / "blender.exe"

def is_installed() -> bool:
    """Check if Blender is already installed."""
    return EXECUTABLE.exists()

def download_blender(force: bool = False) -> Path:
    """Download Blender ZIP file."""
    # Implementation here
    pass

def extract_blender(zip_path: Path) -> None:
    """Extract Blender to installation path."""
    # Implementation here
    pass

def verify_installation() -> bool:
    """Verify Blender can launch."""
    result = subprocess.run(
        [str(EXECUTABLE), "--version"],
        capture_output=True,
        text=True,
        timeout=30
    )
    return "Blender 4.2" in result.stdout
```

### Error Handling

- Network errors during download
- Disk space issues
- Extraction failures
- Verification failures

### Logging

All operations must be logged:

```python
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

def download_blender():
    logger.info("Starting Blender download", extra={"url": BLENDER_URL})
    # ...
    logger.info("Download complete", extra={"size_mb": size})
```

## install_addon.py Requirements

### Functionality

1. Locate Blender's addon directory
2. Symlink or copy `src/blender_addon/` to addon directory
3. Enable addon via Blender command line
4. Verify addon is loaded

### Blender Addon Path

```python
# Windows
addon_path = INSTALL_PATH / "4.2" / "scripts" / "addons" / "aether_bridge"
```

## run_blender_tests.py Requirements

### Functionality

1. Launch Blender in background mode
2. Execute test script inside Blender
3. Capture output and return code
4. Report results to stdout

### Usage

```powershell
python scripts/run_blender_tests.py tests/e2e/test_blender_basic.py
```
