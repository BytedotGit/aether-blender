"""
Blender Socket Client for Aether-Blender Bridge.

This module provides the external Python client that connects to Blender's
socket server to execute code and query scene data.

Features:
- TCP socket connection with configurable timeout
- 4-byte length-prefixed message framing
- JSON-RPC protocol communication
- Thread-safe operation
- Automatic reconnection support
"""

from __future__ import annotations

import contextlib
import socket
import struct
import threading
import time
from typing import Any

from src.bridge.exceptions import (
    ConnectionClosedError,
    ConnectionRefusedError,
    ConnectionTimeoutError,
    ExecutionError,
    MessageFramingError,
    ProtocolError,
)
from src.bridge.protocol import (
    MAX_MESSAGE_SIZE,
    Request,
    Response,
    create_execute_request,
    create_ping_request,
    create_query_request,
)
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

# Default connection settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5005
DEFAULT_TIMEOUT = 10.0  # seconds
DEFAULT_CONNECT_TIMEOUT = 5.0  # seconds
HEADER_SIZE = 4  # 4 bytes for message length prefix
NOT_CONNECTED_MSG = "Not connected"


class BlenderClient:
    """
    Socket client for communicating with Blender addon server.

    Thread-safe client that uses 4-byte length-prefixed message framing
    to prevent message fragmentation issues.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
    ) -> None:
        """
        Initialize BlenderClient.

        Args:
            host: Blender server host address.
            port: Blender server port number.
            timeout: Socket operation timeout in seconds.
            connect_timeout: Connection attempt timeout in seconds.
        """
        logger.debug(
            "Initializing BlenderClient",
            extra={"host": host, "port": port, "timeout": timeout},
        )
        self.host = host
        self.port = port
        self.timeout = timeout
        self.connect_timeout = connect_timeout

        self._socket: socket.socket | None = None
        self._lock = threading.Lock()
        self._connected = False

        logger.debug("BlenderClient initialized")

    @property
    def is_connected(self) -> bool:
        """Check if client is currently connected."""
        return self._connected and self._socket is not None

    def connect(self) -> None:
        """
        Connect to Blender server.

        Raises:
            ConnectionRefusedError: If Blender is not running or addon not active.
            ConnectionTimeoutError: If connection times out.
        """
        logger.debug(
            "Attempting to connect",
            extra={"host": self.host, "port": self.port},
        )

        with self._lock:
            if self._connected:
                logger.debug("Already connected")
                return

            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(self.connect_timeout)
                self._socket.connect((self.host, self.port))
                self._socket.settimeout(self.timeout)
                self._connected = True

                logger.info(
                    "Connected to Blender",
                    extra={"host": self.host, "port": self.port},
                )

            except socket.timeout as err:
                self._cleanup_socket()
                logger.error(
                    "Connection timeout",
                    extra={"host": self.host, "port": self.port},
                )
                raise ConnectionTimeoutError(
                    timeout_seconds=self.connect_timeout,
                    operation="connect",
                    context={"host": self.host, "port": self.port},
                ) from err

            except ConnectionRefusedError as err:
                self._cleanup_socket()
                logger.error(
                    "Connection refused",
                    extra={"host": self.host, "port": self.port},
                )
                raise ConnectionRefusedError(
                    host=self.host,
                    port=self.port,
                    context={"reason": "Blender not running or addon not active"},
                ) from err

            except OSError as err:
                self._cleanup_socket()
                logger.error(
                    "Connection error",
                    extra={"host": self.host, "port": self.port, "error": str(err)},
                )
                raise ConnectionRefusedError(
                    host=self.host,
                    port=self.port,
                    context={"error": str(err)},
                ) from err

    def disconnect(self) -> None:
        """Disconnect from Blender server."""
        logger.debug("Disconnecting from Blender")

        with self._lock:
            self._cleanup_socket()
            logger.info("Disconnected from Blender")

    def _cleanup_socket(self) -> None:
        """Clean up socket resources (internal, must be called with lock held)."""
        if self._socket:
            with contextlib.suppress(OSError):
                self._socket.close()
            self._socket = None
        self._connected = False

    def _send_message(self, data: bytes) -> None:
        """
        Send a message with length prefix.

        Args:
            data: Message bytes to send.

        Raises:
            ConnectionClosedError: If connection is closed.
        """
        if not self._socket:
            raise ConnectionClosedError(reason=NOT_CONNECTED_MSG)

        # Validate message size
        if len(data) > MAX_MESSAGE_SIZE:
            raise ProtocolError(
                f"Message too large: {len(data)} bytes (max {MAX_MESSAGE_SIZE})"
            )

        # Create length-prefixed message
        length_prefix = struct.pack(">I", len(data))
        message = length_prefix + data

        logger.debug(
            "Sending message",
            extra={"data_length": len(data), "total_length": len(message)},
        )

        try:
            self._socket.sendall(message)
        except OSError as err:
            logger.error("Send failed", extra={"error": str(err)})
            self._cleanup_socket()
            raise ConnectionClosedError(reason=str(err)) from err

    def _receive_message(self) -> bytes:
        """
        Receive a length-prefixed message.

        Returns:
            Message bytes.

        Raises:
            ConnectionClosedError: If connection is closed.
            MessageFramingError: If message framing is invalid.
            ConnectionTimeoutError: If receive times out.
        """
        if not self._socket:
            raise ConnectionClosedError(reason=NOT_CONNECTED_MSG)

        try:
            # Read length prefix
            length_bytes = self._recv_exact(HEADER_SIZE)
            if len(length_bytes) != HEADER_SIZE:
                raise MessageFramingError(
                    expected_length=HEADER_SIZE,
                    actual_length=len(length_bytes),
                )

            message_length = struct.unpack(">I", length_bytes)[0]

            # Validate message size
            if message_length > MAX_MESSAGE_SIZE:
                raise ProtocolError(
                    f"Message too large: {message_length} bytes (max {MAX_MESSAGE_SIZE})"
                )

            logger.debug("Receiving message", extra={"expected_length": message_length})

            # Read message body
            message_data = self._recv_exact(message_length)
            if len(message_data) != message_length:
                raise MessageFramingError(
                    expected_length=message_length,
                    actual_length=len(message_data),
                )

            logger.debug("Received message", extra={"actual_length": len(message_data)})
            return message_data

        except socket.timeout as err:
            logger.error("Receive timeout")
            raise ConnectionTimeoutError(
                timeout_seconds=self.timeout,
                operation="receive",
            ) from err

    def _recv_exact(self, num_bytes: int) -> bytes:
        """
        Receive exactly num_bytes from socket.

        Args:
            num_bytes: Number of bytes to receive.

        Returns:
            Received bytes.

        Raises:
            ConnectionClosedError: If connection closes before all bytes received.
        """
        if not self._socket:
            raise ConnectionClosedError(reason=NOT_CONNECTED_MSG)

        data = b""
        while len(data) < num_bytes:
            chunk = self._socket.recv(num_bytes - len(data))
            if not chunk:
                # Connection closed by remote
                raise ConnectionClosedError(reason="Connection closed by remote")
            data += chunk
        return data

    def send_request(self, request: Request) -> Response:
        """
        Send a request and wait for response.

        Args:
            request: Request to send.

        Returns:
            Response from Blender.

        Raises:
            ConnectionClosedError: If not connected.
            ProtocolError: If response is invalid.
        """
        logger.debug(
            "Sending request",
            extra={"id": request.id, "method": request.method.value},
        )

        with self._lock:
            if not self.is_connected:
                raise ConnectionClosedError(reason=NOT_CONNECTED_MSG)

            # Send request
            self._send_message(request.to_bytes())

            # Receive response
            response_data = self._receive_message()
            response = Response.from_bytes(response_data)

            # Validate response ID matches request
            if response.id != request.id:
                raise ProtocolError(
                    f"Response ID mismatch: expected {request.id}, got {response.id}"
                )

            logger.debug(
                "Received response",
                extra={"id": response.id, "status": response.result.status.value},
            )

            return response

    def ping(self) -> float:
        """
        Send a ping to check connection health.

        Returns:
            Round-trip time in seconds.

        Raises:
            ConnectionClosedError: If not connected.
        """
        logger.debug("Sending ping")
        start_time = time.perf_counter()

        request = create_ping_request()
        response = self.send_request(request)

        elapsed = time.perf_counter() - start_time

        if response.is_error:
            logger.warning(
                "Ping returned error", extra={"error": response.result.error}
            )

        logger.debug("Ping successful", extra={"elapsed_seconds": elapsed})
        return elapsed

    def execute(
        self,
        code: str,
        timeout_ms: int = 5000,
    ) -> dict[str, Any]:
        """
        Execute Python code in Blender.

        Args:
            code: Python code to execute.
            timeout_ms: Execution timeout in milliseconds.

        Returns:
            Execution result with data and logs.

        Raises:
            ExecutionError: If code execution fails.
            ConnectionClosedError: If not connected.
        """
        logger.debug(
            "Executing code",
            extra={"code_length": len(code), "timeout_ms": timeout_ms},
        )

        request = create_execute_request(code, timeout_ms)
        response = self.send_request(request)

        if response.is_error:
            logger.error(
                "Execution failed",
                extra={
                    "error": response.result.error,
                    "logs": response.result.logs,
                },
            )
            raise ExecutionError(
                error_message=response.result.error or "Unknown error",
                traceback=response.result.traceback,
                stdout=response.result.logs,
            )

        logger.debug(
            "Execution successful",
            extra={"data_keys": list(response.result.data.keys())},
        )

        return {
            "data": response.result.data,
            "logs": response.result.logs,
        }

    def query(self, query: str) -> dict[str, Any]:
        """
        Query scene information from Blender.

        Args:
            query: Query string (e.g., "objects", "materials").

        Returns:
            Query result data.

        Raises:
            ExecutionError: If query fails.
            ConnectionClosedError: If not connected.
        """
        logger.debug("Querying scene", extra={"query": query})

        request = create_query_request(query)
        response = self.send_request(request)

        if response.is_error:
            logger.error("Query failed", extra={"error": response.result.error})
            raise ExecutionError(
                error_message=response.result.error or "Query failed",
                traceback=response.result.traceback,
            )

        logger.debug("Query successful")
        return response.result.data

    def __enter__(self) -> BlenderClient:
        """Context manager entry - connect to Blender."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit - disconnect from Blender."""
        self.disconnect()
