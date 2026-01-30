"""
Custom Exception Hierarchy for Aether-Blender Bridge.

This module defines all exceptions used in the bridge communication
layer between external Python and Blender's internal environment.
"""

from typing import Any


class AetherError(Exception):
    """Base exception for all Aether-Blender errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """
        Initialize AetherError.

        Args:
            message: Human-readable error description.
            context: Additional context data for debugging.
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """Return string representation with context."""
        if self.context:
            return f"{self.message} | Context: {self.context}"
        return self.message


class BridgeError(AetherError):
    """Base exception for all bridge-related errors."""

    pass


class ConnectionRefusedError(BridgeError):
    """
    Raised when connection to Blender is refused.

    This typically means Blender is not running or the Aether addon
    is not active/registered.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5005,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize ConnectionRefusedError.

        Args:
            host: The host that refused the connection.
            port: The port that was attempted.
            context: Additional context data.
        """
        message = f"Connection refused to Blender at {host}:{port}"
        super().__init__(message, context)
        self.host = host
        self.port = port


class ConnectionTimeoutError(BridgeError):
    """
    Raised when Blender does not respond within the timeout period.

    This may indicate Blender is frozen, processing a long operation,
    or the network is experiencing issues.
    """

    def __init__(
        self,
        timeout_seconds: float,
        operation: str = "unknown",
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize ConnectionTimeoutError.

        Args:
            timeout_seconds: The timeout value that was exceeded.
            operation: Description of the operation that timed out.
            context: Additional context data.
        """
        message = f"Operation '{operation}' timed out after {timeout_seconds}s"
        super().__init__(message, context)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class ProtocolError(BridgeError):
    """
    Raised when a message does not conform to the JSON-RPC protocol.

    This includes invalid JSON, missing required fields, or
    schema validation failures.
    """

    def __init__(
        self,
        reason: str,
        raw_data: str | bytes | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize ProtocolError.

        Args:
            reason: Description of the protocol violation.
            raw_data: The raw data that caused the error.
            context: Additional context data.
        """
        message = f"Protocol error: {reason}"
        super().__init__(message, context)
        self.reason = reason
        self.raw_data = raw_data


class ExecutionError(BridgeError):
    """
    Raised when code execution in Blender fails.

    Contains the traceback and any captured output from the failed
    execution attempt.
    """

    def __init__(
        self,
        error_message: str,
        traceback: str | None = None,
        stdout: str = "",
        stderr: str = "",
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize ExecutionError.

        Args:
            error_message: The error message from execution.
            traceback: Full Python traceback if available.
            stdout: Captured stdout during execution.
            stderr: Captured stderr during execution.
            context: Additional context data.
        """
        message = f"Execution failed: {error_message}"
        super().__init__(message, context)
        self.error_message = error_message
        self.traceback = traceback
        self.stdout = stdout
        self.stderr = stderr


class ConnectionClosedError(BridgeError):
    """
    Raised when the connection to Blender is unexpectedly closed.

    This may indicate Blender crashed or was closed by the user.
    """

    def __init__(
        self,
        reason: str = "Connection closed unexpectedly",
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize ConnectionClosedError.

        Args:
            reason: Description of why the connection closed.
            context: Additional context data.
        """
        super().__init__(reason, context)
        self.reason = reason


class MessageFramingError(BridgeError):
    """
    Raised when message framing is corrupted or invalid.

    This can happen when the 4-byte length prefix doesn't match
    the actual message length, or when the connection is corrupted.
    """

    def __init__(
        self,
        expected_length: int | None = None,
        actual_length: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize MessageFramingError.

        Args:
            expected_length: Expected message length from header.
            actual_length: Actual received message length.
            context: Additional context data.
        """
        if expected_length is not None and actual_length is not None:
            message = (
                f"Message framing error: expected {expected_length} bytes, "
                f"got {actual_length} bytes"
            )
        else:
            message = "Message framing error: invalid message structure"
        super().__init__(message, context)
        self.expected_length = expected_length
        self.actual_length = actual_length
