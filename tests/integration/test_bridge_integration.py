"""
Integration Tests for Blender Addon Bridge.

These tests verify end-to-end communication between the external Python
client and the Blender addon server. They launch Blender in background
mode with the addon enabled and test the socket bridge.

NOTE: These tests require Blender to be installed and may take longer to run.
"""

from __future__ import annotations

import os
import queue
import shutil
import socket
import subprocess
import threading
import time
from collections.abc import Generator
from pathlib import Path

import pytest

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BLENDER_PATH = PROJECT_ROOT / "tools" / "blender" / "blender.exe"
ADDON_SRC = PROJECT_ROOT / "src" / "blender_addon"
BLENDER_ADDONS_DIR = (
    PROJECT_ROOT / "tools" / "blender" / "4.2" / "scripts" / "addons" / "aether_bridge"
)

# Bridge settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5005
STARTUP_TIMEOUT = 15  # seconds to wait for Blender to start

# Storage for Blender process output (module-level for fixture access)
_blender_output_lines: queue.Queue[str] = queue.Queue()


def _drain_stdout(process: subprocess.Popen, output_queue: queue.Queue) -> None:
    """Read stdout from process and store in queue to prevent buffer blocking."""
    try:
        for line in iter(process.stdout.readline, ""):
            if line:
                output_queue.put(line.rstrip())
            else:
                break
    except (ValueError, OSError):
        # Process closed
        pass


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a port is open (server is listening)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result == 0
    except OSError:
        return False


def wait_for_port(
    host: str,
    port: int,
    timeout: float = STARTUP_TIMEOUT,
) -> bool:
    """Wait for a port to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_open(host, port):
            return True
        time.sleep(0.5)
    return False


@pytest.fixture(scope="module")
def install_addon() -> Generator[Path, None, None]:
    """
    Install the addon to Blender's addons directory.

    This fixture copies the addon source to Blender's scripts/addons folder
    and cleans up after the test module completes.
    """
    if not BLENDER_PATH.exists():
        pytest.skip("Blender not installed")

    # Ensure target directory exists
    BLENDER_ADDONS_DIR.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing addon installation (handle both symlink and directory)
    if BLENDER_ADDONS_DIR.is_symlink():
        BLENDER_ADDONS_DIR.unlink()
    elif BLENDER_ADDONS_DIR.exists():
        shutil.rmtree(BLENDER_ADDONS_DIR)

    # Create symlink to addon source (more efficient than copying)
    try:
        BLENDER_ADDONS_DIR.symlink_to(ADDON_SRC, target_is_directory=True)
    except OSError:
        # Fallback to copy if symlink fails (e.g., no admin rights)
        shutil.copytree(ADDON_SRC, BLENDER_ADDONS_DIR)

    yield BLENDER_ADDONS_DIR

    # Cleanup (handle both symlink and directory)
    if BLENDER_ADDONS_DIR.is_symlink():
        BLENDER_ADDONS_DIR.unlink()
    elif BLENDER_ADDONS_DIR.exists():
        shutil.rmtree(BLENDER_ADDONS_DIR)


@pytest.fixture(scope="module")
def blender_with_addon(
    install_addon: Path,
) -> Generator[subprocess.Popen, None, None]:
    """
    Start Blender in background mode with the addon enabled.

    This fixture launches Blender with a startup script that enables
    the addon and keeps Blender running until the test completes.
    """
    # Create startup script that directly imports and registers the addon
    # We add the addons directory to sys.path and import directly
    # rather than using addon_enable which has path resolution issues
    #
    # IMPORTANT: In background mode, bpy.app.timers don't automatically run.
    # We need to manually pump the queue by calling the timer callback directly
    # in our main loop.
    startup_script = f"""
import bpy
import sys
import time

# Add the addons directory to Python path
addon_parent = r'{BLENDER_ADDONS_DIR.parent}'
if addon_parent not in sys.path:
    sys.path.insert(0, addon_parent)

# Import and register the addon directly
try:
    import aether_bridge
    aether_bridge.register()
    print("AETHER_BRIDGE: Addon registered successfully", flush=True)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"AETHER_BRIDGE: Failed to register addon: {{e}}", flush=True)
    sys.exit(1)

print("AETHER_BRIDGE: Server starting, waiting for connections...", flush=True)

# Get reference to the queue handler for manual processing
# Since we're in background mode, bpy.app.timers don't automatically fire
_queue_handler = aether_bridge._queue_handler

# Main loop that manually processes the queue
for i in range(60000):  # Run for up to 10 minutes (at 0.01s per iteration)
    # Manually call the queue handler's timer callback
    # This processes any pending messages in the queue
    if _queue_handler is not None:
        try:
            result = _queue_handler._timer_callback()
        except Exception as e:
            print(f"AETHER_BRIDGE: Timer error: {{e}}", flush=True)

    time.sleep(0.01)  # 10ms instead of 100ms for faster response

    if i % 1000 == 0 and i > 0:  # Every 10 seconds
        print(f"AETHER_BRIDGE: Still running... ({{i // 100}}s)", flush=True)
"""

    startup_file = PROJECT_ROOT / "tests" / "fixtures" / "_test_startup.py"
    startup_file.parent.mkdir(parents=True, exist_ok=True)
    startup_file.write_text(startup_script)

    # Clear any previous output
    while not _blender_output_lines.empty():
        try:
            _blender_output_lines.get_nowait()
        except queue.Empty:
            break

    try:
        # Launch Blender in background with the startup script
        process = subprocess.Popen(
            [
                str(BLENDER_PATH),
                "--background",
                "--python",
                str(startup_file),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )

        # Start a thread to drain stdout to prevent buffer blocking
        drain_thread = threading.Thread(
            target=_drain_stdout,
            args=(process, _blender_output_lines),
            daemon=True,
        )
        drain_thread.start()

        # Wait for the server to start
        if not wait_for_port(DEFAULT_HOST, DEFAULT_PORT, timeout=STARTUP_TIMEOUT):
            # Collect output for debugging
            output_lines = []
            while not _blender_output_lines.empty():
                try:
                    output_lines.append(_blender_output_lines.get_nowait())
                except queue.Empty:
                    break

            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

            pytest.fail(
                f"Blender addon server did not start within {STARTUP_TIMEOUT}s.\n"
                f"Output: {chr(10).join(output_lines)}"
            )

        yield process

    finally:
        # Terminate Blender
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

        # Cleanup startup script
        if startup_file.exists():
            startup_file.unlink()


class TestAddonInstallation:
    """Tests for addon installation verification."""

    def test_addon_source_exists(self) -> None:
        """Test that addon source directory exists."""
        assert ADDON_SRC.exists(), f"Addon source not found: {ADDON_SRC}"

    def test_addon_init_exists(self) -> None:
        """Test that addon __init__.py exists."""
        init_file = ADDON_SRC / "__init__.py"
        assert init_file.exists(), f"Addon __init__.py not found: {init_file}"

    def test_addon_has_bl_info(self) -> None:
        """Test that addon has bl_info defined."""
        init_file = ADDON_SRC / "__init__.py"
        content = init_file.read_text()
        assert "bl_info" in content, "bl_info not found in addon __init__.py"

    @pytest.mark.skipif(
        not BLENDER_PATH.exists(),
        reason="Blender not installed",
    )
    def test_addon_can_be_imported(
        self,
        install_addon: Path,  # noqa: ARG002 - Fixture needed to install addon
    ) -> None:
        """Test that addon can be imported in Blender."""
        python_code = f"""
import sys
sys.path.insert(0, r'{str(BLENDER_ADDONS_DIR.parent)}')
try:
    import aether_bridge
    print(f"IMPORT_SUCCESS: {{aether_bridge.bl_info['name']}}")
except Exception as e:
    print(f"IMPORT_FAILED: {{e}}")
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

        assert (
            "IMPORT_SUCCESS" in result.stdout
        ), f"Addon import failed. stdout: {result.stdout}, stderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.skipif(
    not BLENDER_PATH.exists(),
    reason="Blender not installed",
)
class TestBridgeConnection:
    """Integration tests for bridge connection."""

    @pytest.fixture(scope="class")
    def connected_client(
        self,
        blender_with_addon: subprocess.Popen,  # noqa: ARG002 - Ensures Blender running
    ) -> Generator:
        """
        Provide a connected BlenderClient for the test class.

        This reuses a single connection across all tests in the class
        to avoid connection churn issues.
        """
        from src.bridge.client import BlenderClient

        client = BlenderClient()
        client.connect()
        yield client
        client.disconnect()

    def test_server_port_available(
        self,
        blender_with_addon: subprocess.Popen,  # noqa: ARG002 - Ensures Blender running
    ) -> None:
        """Test that the server is listening on the expected port."""
        assert is_port_open(
            DEFAULT_HOST, DEFAULT_PORT
        ), f"Server not listening on {DEFAULT_HOST}:{DEFAULT_PORT}"

    def test_client_can_connect(
        self,
        blender_with_addon: subprocess.Popen,  # noqa: ARG002 - Ensures Blender running
    ) -> None:
        """Test that a client can establish a socket connection."""
        from src.bridge.client import BlenderClient

        client = BlenderClient()
        try:
            client.connect()
            assert client.is_connected
        finally:
            client.disconnect()

    def test_ping_request(
        self,
        connected_client,
    ) -> None:
        """Test that ping request works."""
        elapsed = connected_client.ping()
        assert elapsed > 0
        assert elapsed < 5.0  # Should respond within 5 seconds

    def test_execute_simple_code(
        self,
        connected_client,
    ) -> None:
        """Test executing simple Python code in Blender."""
        result = connected_client.execute("print('Hello from Blender!')")
        assert "data" in result

    def test_execute_bpy_code(
        self,
        connected_client,
    ) -> None:
        """Test executing bpy code in Blender."""
        result = connected_client.execute("import bpy; print(bpy.app.version_string)")
        assert "data" in result

    def test_query_scene(
        self,
        connected_client,
    ) -> None:
        """Test querying scene information."""
        result = connected_client.query("scene")
        # query() returns the data directly, not wrapped in {"data": ...}
        assert "name" in result
        assert "objects" in result

    def test_context_manager(
        self,
        blender_with_addon: subprocess.Popen,  # noqa: ARG002 - Ensures Blender running
    ) -> None:
        """Test BlenderClient context manager."""
        from src.bridge.client import BlenderClient

        with BlenderClient() as client:
            elapsed = client.ping()
            assert elapsed > 0

    def test_multiple_requests(
        self,
        connected_client,
    ) -> None:
        """Test sending multiple requests in sequence."""
        for _ in range(5):
            elapsed = connected_client.ping()
            assert elapsed > 0
