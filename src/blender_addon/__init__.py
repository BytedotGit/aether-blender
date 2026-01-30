"""
Aether Bridge - Blender Addon.

This addon provides a socket server that accepts connections from the
external Aether Python client and executes code on Blender's main thread.

CRITICAL: This code runs inside Blender's Python environment.
All bpy operations MUST occur on the main thread.
"""

bl_info = {
    "name": "Aether Bridge",
    "author": "Aether Team",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Aether",
    "description": "Socket bridge for Aether-Blender natural language interface",
    "category": "Development",
    "doc_url": "https://github.com/BytedotGit/aether-blender",
    "tracker_url": "https://github.com/BytedotGit/aether-blender/issues",
}

import logging  # noqa: E402
from pathlib import Path  # noqa: E402

# Configure logging for addon (runs inside Blender)
_addon_logger: logging.Logger | None = None


def _get_addon_logger() -> logging.Logger:
    """Get or create addon logger."""
    global _addon_logger
    if _addon_logger is None:
        _addon_logger = logging.getLogger("aether_bridge")
        _addon_logger.setLevel(logging.DEBUG)

        # Console handler
        if not _addon_logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
            )
            handler.setFormatter(formatter)
            _addon_logger.addHandler(handler)

    return _addon_logger


# Module-level state
_server = None
_queue_handler = None


def register() -> None:
    """
    Register the Aether Bridge addon.

    Called by Blender when the addon is enabled.
    Starts the socket server and queue handler.
    """
    logger = _get_addon_logger()
    logger.info("Registering Aether Bridge addon")

    try:
        # Import here to avoid issues if addon files aren't fully loaded
        from . import queue_handler, server

        global _server, _queue_handler

        # Start queue handler (processes messages on main thread)
        _queue_handler = queue_handler.QueueHandler()
        _queue_handler.start()
        logger.info("Queue handler started")

        # Start socket server (listens in background thread)
        _server = server.SocketServer(message_handler=_queue_handler.enqueue)
        _server.start()
        logger.info("Socket server started")

        logger.info("Aether Bridge addon registered successfully")

    except Exception as e:
        logger.critical(f"Failed to register Aether Bridge: {e}")
        raise


def unregister() -> None:
    """
    Unregister the Aether Bridge addon.

    Called by Blender when the addon is disabled.
    Stops the socket server and cleans up resources.
    """
    logger = _get_addon_logger()
    logger.info("Unregistering Aether Bridge addon")

    global _server, _queue_handler

    try:
        # Stop socket server first
        if _server is not None:
            _server.stop()
            _server = None
            logger.info("Socket server stopped")

        # Stop queue handler
        if _queue_handler is not None:
            _queue_handler.stop()
            _queue_handler = None
            logger.info("Queue handler stopped")

        logger.info("Aether Bridge addon unregistered successfully")

    except Exception as e:
        logger.error(f"Error during unregister: {e}")


# For Blender's addon system
if __name__ == "__main__":
    register()
