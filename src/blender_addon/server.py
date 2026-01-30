"""
Threaded Socket Server for Aether Bridge.

This module runs inside Blender and listens for connections from the
external Aether Python client. It handles message framing and delegates
execution to the queue handler for main thread processing.

CRITICAL: This server runs in a background thread. Do NOT call bpy
functions from this module. All bpy operations are delegated via queue.
"""

from __future__ import annotations

import contextlib
import json
import logging
import socket
import struct
import threading
from collections.abc import Callable
from typing import Any

# Protocol constants (must match client)
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5005
HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB
SOCKET_TIMEOUT = 1.0  # Short timeout for checking shutdown flag

logger = logging.getLogger("aether_bridge.server")


class ClientHandler:
    """Handles a single client connection."""

    def __init__(
        self,
        client_socket: socket.socket,
        client_address: tuple[str, int],
        message_handler: Callable[
            [dict[str, Any], Callable[[dict[str, Any]], None]], None
        ],
    ) -> None:
        """
        Initialize client handler.

        Args:
            client_socket: Connected client socket.
            client_address: Client address tuple (host, port).
            message_handler: Callback to handle messages (passes response callback).
        """
        logger.debug(f"ClientHandler init for {client_address}")
        self.socket = client_socket
        self.address = client_address
        self.message_handler = message_handler
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start handling client in background thread."""
        logger.debug(f"Starting client handler for {self.address}")
        self._running = True
        self._thread = threading.Thread(
            target=self._handle_client,
            name=f"aether-client-{self.address[1]}",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop handling client."""
        logger.debug(f"Stopping client handler for {self.address}")
        self._running = False
        with contextlib.suppress(OSError):
            self.socket.close()

    def _handle_client(self) -> None:
        """Main client handling loop."""
        logger.info(f"Handling client {self.address}")

        try:
            self.socket.settimeout(SOCKET_TIMEOUT)

            while self._running:
                try:
                    message = self._receive_message()
                    if message is None:
                        break

                    logger.debug(f"Received message from {self.address}")

                    # Create response callback that sends response to this client
                    def send_response(response: dict[str, Any]) -> None:
                        try:
                            self._send_message(response)
                        except Exception as e:
                            logger.error(f"Failed to send response: {e}")

                    # Delegate to message handler (will be processed on main thread)
                    self.message_handler(message, send_response)

                except socket.timeout:
                    # Timeout is normal - allows checking _running flag
                    continue

        except Exception as e:
            print(f"DEBUG SERVER: Client handler error: {e}", flush=True)
            logger.error(f"Client handler error for {self.address}: {e}")

        finally:
            logger.info(f"Client {self.address} disconnected")
            with contextlib.suppress(OSError):
                self.socket.close()

    def _receive_message(self) -> dict[str, Any] | None:
        """
        Receive a length-prefixed JSON message.

        Returns:
            Parsed message dict or None if connection closed.
        """
        # Read length prefix
        length_bytes = self._recv_exact(HEADER_SIZE)
        if length_bytes is None or len(length_bytes) != HEADER_SIZE:
            return None

        message_length = struct.unpack(">I", length_bytes)[0]

        # Validate message size
        if message_length > MAX_MESSAGE_SIZE:
            logger.error(f"Message too large: {message_length} bytes")
            return None

        # Read message body
        message_bytes = self._recv_exact(message_length)
        if message_bytes is None or len(message_bytes) != message_length:
            return None

        # Parse JSON
        try:
            return json.loads(message_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse message: {e}")
            return None

    def _recv_exact(self, num_bytes: int) -> bytes | None:
        """
        Receive exactly num_bytes from socket.

        Returns:
            Received bytes or None if connection closed.
        """
        data = b""
        while len(data) < num_bytes:
            try:
                chunk = self.socket.recv(num_bytes - len(data))
                if not chunk:
                    return None  # Connection closed
                data += chunk
            except socket.timeout:
                if not self._running:
                    return None
                continue
            except OSError:
                return None
        return data

    def _send_message(self, message: dict[str, Any]) -> None:
        """Send a length-prefixed JSON message."""
        message_bytes = json.dumps(message).encode("utf-8")
        length_prefix = struct.pack(">I", len(message_bytes))

        with self._lock:
            self.socket.sendall(length_prefix + message_bytes)


class SocketServer:
    """
    Threaded socket server for Aether Bridge.

    Listens for connections and spawns client handlers.
    """

    def __init__(
        self,
        message_handler: Callable[
            [dict[str, Any], Callable[[dict[str, Any]], None]], None
        ],
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
    ) -> None:
        """
        Initialize socket server.

        Args:
            message_handler: Callback to handle incoming messages.
            host: Host address to bind to.
            port: Port number to bind to.
        """
        logger.debug(f"SocketServer init on {host}:{port}")
        self.host = host
        self.port = port
        self.message_handler = message_handler

        self._server_socket: socket.socket | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._clients: list[ClientHandler] = []
        self._clients_lock = threading.Lock()

    def start(self) -> None:
        """Start the socket server in a background thread."""
        logger.info(f"Starting socket server on {self.host}:{self.port}")

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.settimeout(SOCKET_TIMEOUT)

        try:
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(5)
        except OSError as e:
            logger.error(f"Failed to bind server socket: {e}")
            raise

        self._running = True
        self._thread = threading.Thread(
            target=self._accept_loop,
            name="aether-server",
            daemon=True,
        )
        self._thread.start()

        logger.info(f"Socket server listening on {self.host}:{self.port}")

    def stop(self) -> None:
        """Stop the socket server and all client handlers."""
        logger.info("Stopping socket server")
        self._running = False

        # Stop all clients
        with self._clients_lock:
            for client in self._clients:
                client.stop()
            self._clients.clear()

        # Close server socket
        if self._server_socket:
            with contextlib.suppress(OSError):
                self._server_socket.close()
            self._server_socket = None

        # Wait for server thread
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        logger.info("Socket server stopped")

    def _accept_loop(self) -> None:
        """Main loop accepting client connections."""
        logger.debug("Accept loop started")

        while self._running and self._server_socket:
            try:
                client_socket, client_address = self._server_socket.accept()
                logger.info(f"New connection from {client_address}")

                # Create and start client handler
                handler = ClientHandler(
                    client_socket=client_socket,
                    client_address=client_address,
                    message_handler=self.message_handler,
                )
                handler.start()

                with self._clients_lock:
                    self._clients.append(handler)
                    # Clean up finished handlers
                    self._clients = [c for c in self._clients if c._running]

            except socket.timeout:
                # Timeout is normal - allows checking _running flag
                continue
            except OSError as e:
                if self._running:
                    logger.error(f"Accept error: {e}")
                break

        logger.debug("Accept loop ended")

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        with self._clients_lock:
            return len([c for c in self._clients if c._running])
