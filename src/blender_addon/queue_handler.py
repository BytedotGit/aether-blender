"""
Main Thread Queue Handler for Aether Bridge.

This module manages the message queue and processes messages on Blender's
main thread using bpy.app.timers. This is essential because Blender's
bpy module is NOT thread-safe.

Architecture:
1. Socket server (background thread) receives messages
2. Messages are queued via enqueue()
3. Timer callback processes queue on main thread
4. Responses are sent back via callback
"""

from __future__ import annotations

import logging
import queue
from collections.abc import Callable
from typing import Any

# Blender imports (may not be available outside Blender)
try:
    import bpy

    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    bpy = None  # type: ignore

from . import executor

logger = logging.getLogger("aether_bridge.queue_handler")

# Protocol constants
JSONRPC_VERSION = "2.0"
TIMER_INTERVAL = 0.1  # Check queue every 100ms

# Message methods
METHOD_PING = "ping"
METHOD_EXECUTE_CODE = "execute_code"
METHOD_QUERY_SCENE = "query_scene"
METHOD_GET_OBJECTS = "get_objects"
METHOD_SHUTDOWN = "shutdown"


class QueuedMessage:
    """A queued message with its response callback."""

    def __init__(
        self,
        message: dict[str, Any],
        response_callback: Callable[[dict[str, Any]], None],
    ) -> None:
        """
        Initialize queued message.

        Args:
            message: The JSON-RPC message.
            response_callback: Function to call with response.
        """
        self.message = message
        self.response_callback = response_callback


class QueueHandler:
    """
    Processes messages on Blender's main thread.

    Uses bpy.app.timers to periodically check a thread-safe queue
    and process messages that require bpy access.
    """

    def __init__(self) -> None:
        """Initialize queue handler."""
        logger.debug("Initializing QueueHandler")
        self._queue: queue.Queue[QueuedMessage] = queue.Queue()
        self._running = False
        self._timer_registered = False

    def start(self) -> None:
        """Start processing the message queue."""
        logger.info("Starting queue handler")

        if not BLENDER_AVAILABLE:
            logger.warning("Blender not available - queue handler in mock mode")
            self._running = True
            return

        self._running = True
        self._register_timer()
        logger.info("Queue handler started")

    def stop(self) -> None:
        """Stop processing the message queue."""
        logger.info("Stopping queue handler")
        self._running = False

        if BLENDER_AVAILABLE:
            self._unregister_timer()

        # Clear the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

        logger.info("Queue handler stopped")

    def enqueue(
        self,
        message: dict[str, Any],
        response_callback: Callable[[dict[str, Any]], None],
    ) -> None:
        """
        Enqueue a message for processing on the main thread.

        Args:
            message: The JSON-RPC message to process.
            response_callback: Function to call with the response.

        Note:
            This method is thread-safe and can be called from any thread.
        """
        logger.debug("Enqueuing message", extra={"method": message.get("method")})
        queued = QueuedMessage(message, response_callback)
        self._queue.put(queued)

    def _register_timer(self) -> None:
        """Register the timer callback with Blender."""
        if not BLENDER_AVAILABLE or self._timer_registered:
            return

        try:
            bpy.app.timers.register(
                self._timer_callback,
                first_interval=TIMER_INTERVAL,
                persistent=True,
            )
            self._timer_registered = True
            logger.debug("Timer registered")
        except Exception as e:
            logger.error(f"Failed to register timer: {e}")

    def _unregister_timer(self) -> None:
        """Unregister the timer callback from Blender."""
        if not BLENDER_AVAILABLE or not self._timer_registered:
            return

        try:
            if bpy.app.timers.is_registered(self._timer_callback):
                bpy.app.timers.unregister(self._timer_callback)
            self._timer_registered = False
            logger.debug("Timer unregistered")
        except Exception as e:
            logger.error(f"Failed to unregister timer: {e}")

    def _timer_callback(self) -> float | None:
        """
        Timer callback that processes queued messages.

        This runs on Blender's main thread, making it safe to use bpy.

        Returns:
            Time until next call, or None to unregister.
        """
        if not self._running:
            logger.debug("Timer stopping - handler not running")
            self._timer_registered = False
            return None

        # Process all available messages
        messages_processed = 0
        max_per_tick = 10  # Limit to avoid blocking Blender too long

        while messages_processed < max_per_tick:
            try:
                queued = self._queue.get_nowait()
                self._process_message(queued)
                messages_processed += 1
            except queue.Empty:
                break

        if messages_processed > 0:
            logger.debug(f"Processed {messages_processed} messages")

        return TIMER_INTERVAL

    def _process_message(self, queued: QueuedMessage) -> None:
        """
        Process a single queued message.

        Args:
            queued: The queued message with callback.
        """
        message = queued.message
        request_id = message.get("id", "unknown")
        method = message.get("method", "unknown")

        logger.debug("Processing message", extra={"id": request_id, "method": method})

        try:
            response = self._handle_method(message)
            queued.response_callback(response)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = self._create_error_response(
                request_id=request_id,
                error=str(e),
            )
            queued.response_callback(error_response)

    def _handle_method(self, message: dict[str, Any]) -> dict[str, Any]:
        """
        Handle a specific RPC method.

        Args:
            message: The JSON-RPC message.

        Returns:
            Response dictionary.
        """
        request_id = message.get("id", "unknown")
        method = message.get("method", "")
        params = message.get("params", {})

        if method == METHOD_PING:
            return self._handle_ping(request_id)

        elif method == METHOD_EXECUTE_CODE:
            return self._handle_execute_code(request_id, params)

        elif method == METHOD_QUERY_SCENE:
            return self._handle_query_scene(request_id, params)

        elif method == METHOD_GET_OBJECTS:
            return self._handle_get_objects(request_id)

        elif method == METHOD_SHUTDOWN:
            return self._handle_shutdown(request_id)

        else:
            return self._create_error_response(
                request_id=request_id,
                error=f"Unknown method: {method}",
            )

    def _handle_ping(self, request_id: str) -> dict[str, Any]:
        """Handle ping request."""
        logger.debug("Handling ping")
        return self._create_success_response(
            request_id=request_id,
            data={"pong": True},
        )

    def _handle_execute_code(
        self,
        request_id: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle code execution request."""
        code = params.get("code", "")
        logger.debug("Handling execute_code", extra={"code_length": len(code)})

        if not code:
            return self._create_error_response(
                request_id=request_id,
                error="No code provided",
            )

        result = executor.execute_code(code)

        if result.success:
            return self._create_success_response(
                request_id=request_id,
                data=result.to_dict().get("data", {}),
                logs=result.stdout,
            )
        else:
            return self._create_error_response(
                request_id=request_id,
                error=result.error or "Execution failed",
                traceback=result.traceback_str,
                logs=result.stdout,
            )

    def _handle_query_scene(
        self,
        request_id: str,
        params: dict[str, Any],  # noqa: ARG002 - Reserved for future query options
    ) -> dict[str, Any]:
        """Handle scene query request."""
        logger.debug("Handling query_scene")

        scene_info = executor.get_scene_info()

        if "error" in scene_info:
            return self._create_error_response(
                request_id=request_id,
                error=scene_info["error"],
            )

        return self._create_success_response(
            request_id=request_id,
            data=scene_info,
        )

    def _handle_get_objects(self, request_id: str) -> dict[str, Any]:
        """Handle get objects request."""
        logger.debug("Handling get_objects")

        objects = executor.get_object_list()

        return self._create_success_response(
            request_id=request_id,
            data={"objects": objects},
        )

    def _handle_shutdown(self, request_id: str) -> dict[str, Any]:
        """Handle shutdown request (for graceful addon disable)."""
        logger.info("Shutdown requested")
        # Note: Actual shutdown is handled by addon unregister
        return self._create_success_response(
            request_id=request_id,
            data={"shutdown": True},
        )

    def _create_success_response(
        self,
        request_id: str,
        data: dict[str, Any] | None = None,
        logs: str = "",
    ) -> dict[str, Any]:
        """Create a success response."""
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "result": {
                "status": "success",
                "data": data or {},
                "logs": logs,
            },
        }

    def _create_error_response(
        self,
        request_id: str,
        error: str,
        traceback: str | None = None,
        logs: str = "",
    ) -> dict[str, Any]:
        """Create an error response."""
        result: dict[str, Any] = {
            "status": "error",
            "data": {},
            "logs": logs,
            "error": error,
        }
        if traceback:
            result["traceback"] = traceback

        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "result": result,
        }

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    @property
    def is_running(self) -> bool:
        """Check if handler is running."""
        return self._running
