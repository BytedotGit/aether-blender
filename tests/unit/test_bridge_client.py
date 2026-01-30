"""
Unit Tests for Bridge Client Module.

Tests socket client connection, message framing, and error handling.
Uses mock sockets to test without requiring a running Blender instance.
"""

from __future__ import annotations

import socket
import struct
import threading
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.bridge.client import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    HEADER_SIZE,
    BlenderClient,
)
from src.bridge.exceptions import (
    ConnectionClosedError,
    ConnectionRefusedError,
    ConnectionTimeoutError,
    ExecutionError,
    ProtocolError,
)
from src.bridge.protocol import (
    MessageMethod,
    Request,
    create_success_response,
)


class TestBlenderClientInit:
    """Tests for BlenderClient initialization."""

    def test_default_values(self) -> None:
        """Test that client initializes with default values."""
        client = BlenderClient()

        assert client.host == DEFAULT_HOST
        assert client.port == DEFAULT_PORT
        assert abs(client.timeout - 10.0) < 0.001
        assert abs(client.connect_timeout - 5.0) < 0.001
        assert client.is_connected is False

    def test_custom_values(self) -> None:
        """Test that client accepts custom values."""
        client = BlenderClient(
            host="192.168.1.1",
            port=9999,
            timeout=30.0,
            connect_timeout=10.0,
        )

        assert client.host == "192.168.1.1"
        assert client.port == 9999
        assert abs(client.timeout - 30.0) < 0.001
        assert abs(client.connect_timeout - 10.0) < 0.001


class TestBlenderClientConnect:
    """Tests for BlenderClient connection methods."""

    def test_connect_success(self) -> None:
        """Test successful connection."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            mock_socket.connect.assert_called_once_with((DEFAULT_HOST, DEFAULT_PORT))
            assert client.is_connected is True

    def test_connect_already_connected(self) -> None:
        """Test that connecting when already connected is a no-op."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()
            client.connect()  # Second call should be no-op

            # connect should only be called once
            assert mock_socket.connect.call_count == 1

    def test_connect_refused(self) -> None:
        """Test connection refused error."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.connect.side_effect = ConnectionRefusedError(
                "Connection refused"
            )
            mock_socket_class.return_value = mock_socket

            with pytest.raises(ConnectionRefusedError):
                client.connect()

            assert client.is_connected is False

    def test_connect_timeout(self) -> None:
        """Test connection timeout error."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.connect.side_effect = socket.timeout("timed out")
            mock_socket_class.return_value = mock_socket

            with pytest.raises(ConnectionTimeoutError) as exc_info:
                client.connect()

            assert exc_info.value.operation == "connect"
            assert client.is_connected is False

    def test_disconnect(self) -> None:
        """Test disconnection."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()
            assert client.is_connected is True

            client.disconnect()

            mock_socket.close.assert_called()
            assert client.is_connected is False

    def test_disconnect_when_not_connected(self) -> None:
        """Test disconnecting when not connected is safe."""
        client = BlenderClient()
        client.disconnect()  # Should not raise

        assert client.is_connected is False


class TestBlenderClientContextManager:
    """Tests for BlenderClient context manager."""

    def test_context_manager_connects_and_disconnects(self) -> None:
        """Test that context manager connects on entry and disconnects on exit."""
        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            with BlenderClient() as client:
                assert client.is_connected is True

            mock_socket.close.assert_called()

    def test_context_manager_disconnects_on_exception(self) -> None:
        """Test that context manager disconnects even on exception."""
        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            with pytest.raises(ValueError), BlenderClient() as client:
                assert client.is_connected is True
                raise ValueError("Test exception")

            mock_socket.close.assert_called()


class TestMessageFraming:
    """Tests for message framing (4-byte length prefix)."""

    def test_send_message_framing(self) -> None:
        """Test that messages are sent with correct length prefix."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            # Access private method for testing
            test_data = b'{"test": "data"}'
            client._send_message(test_data)

            # Verify sendall was called with length prefix + data
            call_args = mock_socket.sendall.call_args[0][0]
            expected_prefix = struct.pack(">I", len(test_data))
            assert call_args == expected_prefix + test_data

    def test_receive_message_framing(self) -> None:
        """Test that messages are received with correct length handling."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            # Prepare mock response
            response_data = (
                b'{"jsonrpc": "2.0", "id": "test", "result": {"status": "success"}}'
            )
            length_prefix = struct.pack(">I", len(response_data))

            # Mock recv to return length prefix then data
            mock_socket.recv.side_effect = [length_prefix, response_data]

            result = client._receive_message()

            assert result == response_data

    def test_receive_message_fragmented(self) -> None:
        """Test receiving fragmented message."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            response_data = (
                b'{"jsonrpc": "2.0", "id": "test", "result": {"status": "success"}}'
            )
            length_prefix = struct.pack(">I", len(response_data))

            # Simulate fragmented receive (2 bytes at a time for header, then data in chunks)
            mock_socket.recv.side_effect = [
                length_prefix[:2],  # First 2 bytes of header
                length_prefix[2:],  # Last 2 bytes of header
                response_data[:10],  # First chunk of data
                response_data[10:],  # Rest of data
            ]

            result = client._receive_message()

            assert result == response_data


class TestBlenderClientOperations:
    """Tests for BlenderClient high-level operations."""

    def _create_mock_response(
        self,
        request_id: str,
        success: bool = True,
        data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> bytes:
        """Create a mock response as bytes with framing."""
        if success:
            response = create_success_response(request_id, data or {})
        else:
            from src.bridge.protocol import create_error_response

            response = create_error_response(request_id, error or "Error")

        response_bytes = response.to_bytes()
        length_prefix = struct.pack(">I", len(response_bytes))
        return length_prefix + response_bytes

    def test_ping_success(self) -> None:
        """Test successful ping."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            # We need to capture the request ID from send to match response
            sent_data = []

            def capture_send(data: bytes) -> None:
                sent_data.append(data)

            mock_socket.sendall.side_effect = capture_send

            # Create response after request is captured
            def mock_recv(size: int) -> bytes:
                if not sent_data:
                    return b""

                # Parse request ID from sent data
                import json

                request_bytes = sent_data[0][HEADER_SIZE:]
                request = json.loads(request_bytes)
                request_id = request["id"]

                response = self._create_mock_response(
                    request_id, success=True, data={"pong": True}
                )

                if size == HEADER_SIZE:
                    return response[:HEADER_SIZE]
                return response[HEADER_SIZE:]

            mock_socket.recv.side_effect = mock_recv

            elapsed = client.ping()

            assert elapsed >= 0
            assert isinstance(elapsed, float)

    def test_execute_success(self) -> None:
        """Test successful code execution."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            sent_data = []
            mock_socket.sendall.side_effect = lambda d: sent_data.append(d)

            def mock_recv(size: int) -> bytes:
                if not sent_data:
                    return b""

                import json

                request_bytes = sent_data[0][HEADER_SIZE:]
                request = json.loads(request_bytes)
                request_id = request["id"]

                response = self._create_mock_response(
                    request_id, success=True, data={"executed": True}
                )

                if size == HEADER_SIZE:
                    return response[:HEADER_SIZE]
                return response[HEADER_SIZE:]

            mock_socket.recv.side_effect = mock_recv

            result = client.execute("print('hello')")

            assert "data" in result
            assert result["data"]["executed"] is True

    def test_execute_error(self) -> None:
        """Test code execution error."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            sent_data = []
            mock_socket.sendall.side_effect = lambda d: sent_data.append(d)

            def mock_recv(size: int) -> bytes:
                if not sent_data:
                    return b""

                import json

                request_bytes = sent_data[0][HEADER_SIZE:]
                request = json.loads(request_bytes)
                request_id = request["id"]

                response = self._create_mock_response(
                    request_id, success=False, error="SyntaxError: invalid syntax"
                )

                if size == HEADER_SIZE:
                    return response[:HEADER_SIZE]
                return response[HEADER_SIZE:]

            mock_socket.recv.side_effect = mock_recv

            with pytest.raises(ExecutionError) as exc_info:
                client.execute("invalid python code (")

            assert "SyntaxError" in str(exc_info.value)

    def test_query_success(self) -> None:
        """Test successful query."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            sent_data = []
            mock_socket.sendall.side_effect = lambda d: sent_data.append(d)

            def mock_recv(size: int) -> bytes:
                if not sent_data:
                    return b""

                import json

                request_bytes = sent_data[0][HEADER_SIZE:]
                request = json.loads(request_bytes)
                request_id = request["id"]

                response = self._create_mock_response(
                    request_id, success=True, data={"objects": ["Cube", "Camera"]}
                )

                if size == HEADER_SIZE:
                    return response[:HEADER_SIZE]
                return response[HEADER_SIZE:]

            mock_socket.recv.side_effect = mock_recv

            result = client.query("objects")

            assert result["objects"] == ["Cube", "Camera"]


class TestBlenderClientErrors:
    """Tests for BlenderClient error handling."""

    def test_send_when_not_connected(self) -> None:
        """Test that sending when not connected raises error."""
        client = BlenderClient()

        with pytest.raises(ConnectionClosedError):
            client.ping()

    def test_send_request_when_not_connected(self) -> None:
        """Test that send_request when not connected raises error."""
        client = BlenderClient()
        request = Request(method=MessageMethod.PING, id="test")

        with pytest.raises(ConnectionClosedError):
            client.send_request(request)

    def test_receive_timeout(self) -> None:
        """Test receive timeout handling."""
        client = BlenderClient(timeout=0.1)

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            # Mock recv to timeout
            mock_socket.recv.side_effect = socket.timeout("timed out")
            mock_socket.sendall.return_value = None

            with pytest.raises(ConnectionTimeoutError) as exc_info:
                client.ping()

            assert exc_info.value.operation == "receive"

    def test_connection_closed_during_receive(self) -> None:
        """Test handling of connection closed during receive."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            # Mock recv to return empty (connection closed)
            mock_socket.recv.return_value = b""
            mock_socket.sendall.return_value = None

            with pytest.raises(ConnectionClosedError):
                client.ping()

    def test_response_id_mismatch(self) -> None:
        """Test that response ID mismatch raises error."""
        client = BlenderClient()

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            mock_socket.sendall.return_value = None

            # Create response with wrong ID
            wrong_response = create_success_response("wrong-id", {})
            response_bytes = wrong_response.to_bytes()
            length_prefix = struct.pack(">I", len(response_bytes))

            mock_socket.recv.side_effect = [length_prefix, response_bytes]

            with pytest.raises(ProtocolError) as exc_info:
                client.ping()

            assert "mismatch" in str(exc_info.value)


class TestThreadSafety:
    """Tests for thread safety of BlenderClient."""

    def test_concurrent_access(self) -> None:
        """Test that client handles concurrent access safely."""
        client = BlenderClient()
        errors: list[Exception] = []

        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            client.connect()

            lock = threading.Lock()
            call_count = [0]

            def mock_sendall(data: bytes) -> None:
                with lock:
                    call_count[0] += 1
                    time.sleep(0.01)  # Simulate network delay

            mock_socket.sendall.side_effect = mock_sendall

            # Create proper response
            def mock_recv(size: int) -> bytes:
                response = create_success_response("any-id", {"pong": True})
                response_bytes = response.to_bytes()
                length_prefix = struct.pack(">I", len(response_bytes))

                if size == HEADER_SIZE:
                    return length_prefix
                return response_bytes

            mock_socket.recv.side_effect = mock_recv

            def worker() -> None:
                try:
                    # Note: This won't fully work due to ID mismatch,
                    # but we're testing that concurrent access doesn't crash
                    client.ping()
                except Exception as e:
                    errors.append(e)

            # Start multiple threads
            threads = [threading.Thread(target=worker) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Errors are expected due to ID mismatch in mock,
            # but no deadlock or crash should occur
            assert call_count[0] >= 1  # At least one call made it through
