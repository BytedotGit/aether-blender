"""
JSON-RPC Protocol Implementation for Aether-Blender Bridge.

This module defines the message schema and validation for communication
between the external Python client and the Blender addon server.

Protocol follows JSON-RPC 2.0 specification with custom extensions.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from src.bridge.exceptions import ProtocolError
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

# Protocol constants
JSONRPC_VERSION = "2.0"
DEFAULT_TIMEOUT_MS = 5000
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB


class MessageMethod(str, Enum):
    """Available RPC methods."""

    PING = "ping"
    EXECUTE_CODE = "execute_code"
    QUERY_SCENE = "query_scene"
    GET_OBJECTS = "get_objects"
    SHUTDOWN = "shutdown"


class ResponseStatus(str, Enum):
    """Response status values."""

    SUCCESS = "success"
    ERROR = "error"


@dataclass
class RequestParams:
    """Parameters for an RPC request."""

    code: str | None = None
    timeout: int = DEFAULT_TIMEOUT_MS
    query: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Request:
    """JSON-RPC request message."""

    method: MessageMethod
    params: RequestParams = field(default_factory=RequestParams)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    jsonrpc: str = JSONRPC_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Convert request to dictionary for JSON serialization."""
        logger.debug("Converting request to dict", extra={"id": self.id})
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": (
                self.method.value if isinstance(self.method, Enum) else self.method
            ),
            "params": asdict(self.params),
        }

    def to_json(self) -> str:
        """Serialize request to JSON string."""
        logger.debug("Serializing request to JSON", extra={"id": self.id})
        return json.dumps(self.to_dict())

    def to_bytes(self) -> bytes:
        """Serialize request to bytes with UTF-8 encoding."""
        return self.to_json().encode("utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Request:
        """
        Create Request from dictionary.

        Args:
            data: Dictionary containing request data.

        Returns:
            Request instance.

        Raises:
            ProtocolError: If the data is invalid.
        """
        logger.debug(
            "Parsing request from dict", extra={"data_keys": list(data.keys())}
        )

        # Validate required fields
        if data.get("jsonrpc") != JSONRPC_VERSION:
            raise ProtocolError(
                f"Invalid jsonrpc version: {data.get('jsonrpc')}",
                raw_data=str(data),
            )

        if "method" not in data:
            raise ProtocolError("Missing required field: method", raw_data=str(data))

        if "id" not in data:
            raise ProtocolError("Missing required field: id", raw_data=str(data))

        # Parse method
        try:
            method = MessageMethod(data["method"])
        except ValueError as err:
            raise ProtocolError(
                f"Unknown method: {data['method']}",
                raw_data=str(data),
            ) from err

        # Parse params
        params_data = data.get("params", {})
        params = RequestParams(
            code=params_data.get("code"),
            timeout=params_data.get("timeout", DEFAULT_TIMEOUT_MS),
            query=params_data.get("query"),
            extra=params_data.get("extra", {}),
        )

        return cls(
            jsonrpc=data["jsonrpc"],
            id=data["id"],
            method=method,
            params=params,
        )

    @classmethod
    def from_json(cls, json_str: str) -> Request:
        """
        Parse Request from JSON string.

        Args:
            json_str: JSON string to parse.

        Returns:
            Request instance.

        Raises:
            ProtocolError: If the JSON is invalid or doesn't match schema.
        """
        logger.debug("Parsing request from JSON")
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as err:
            raise ProtocolError(f"Invalid JSON: {err}", raw_data=json_str) from err

        return cls.from_dict(data)

    @classmethod
    def from_bytes(cls, data: bytes) -> Request:
        """Parse Request from bytes."""
        return cls.from_json(data.decode("utf-8"))


@dataclass
class ResponseResult:
    """Result payload for an RPC response."""

    status: ResponseStatus
    data: dict[str, Any] = field(default_factory=dict)
    logs: str = ""
    error: str | None = None
    traceback: str | None = None


@dataclass
class Response:
    """JSON-RPC response message."""

    id: str
    result: ResponseResult
    jsonrpc: str = JSONRPC_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary for JSON serialization."""
        logger.debug("Converting response to dict", extra={"id": self.id})
        result_dict = {
            "status": (
                self.result.status.value
                if isinstance(self.result.status, Enum)
                else self.result.status
            ),
            "data": self.result.data,
            "logs": self.result.logs,
        }
        if self.result.error:
            result_dict["error"] = self.result.error
        if self.result.traceback:
            result_dict["traceback"] = self.result.traceback

        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "result": result_dict,
        }

    def to_json(self) -> str:
        """Serialize response to JSON string."""
        logger.debug("Serializing response to JSON", extra={"id": self.id})
        return json.dumps(self.to_dict())

    def to_bytes(self) -> bytes:
        """Serialize response to bytes with UTF-8 encoding."""
        return self.to_json().encode("utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Response:
        """
        Create Response from dictionary.

        Args:
            data: Dictionary containing response data.

        Returns:
            Response instance.

        Raises:
            ProtocolError: If the data is invalid.
        """
        logger.debug(
            "Parsing response from dict", extra={"data_keys": list(data.keys())}
        )

        # Validate required fields
        if data.get("jsonrpc") != JSONRPC_VERSION:
            raise ProtocolError(
                f"Invalid jsonrpc version: {data.get('jsonrpc')}",
                raw_data=str(data),
            )

        if "id" not in data:
            raise ProtocolError("Missing required field: id", raw_data=str(data))

        if "result" not in data:
            raise ProtocolError("Missing required field: result", raw_data=str(data))

        # Parse result
        result_data = data["result"]
        try:
            status = ResponseStatus(result_data.get("status", "error"))
        except ValueError as err:
            raise ProtocolError(
                f"Invalid status: {result_data.get('status')}",
                raw_data=str(data),
            ) from err

        result = ResponseResult(
            status=status,
            data=result_data.get("data", {}),
            logs=result_data.get("logs", ""),
            error=result_data.get("error"),
            traceback=result_data.get("traceback"),
        )

        return cls(
            jsonrpc=data["jsonrpc"],
            id=data["id"],
            result=result,
        )

    @classmethod
    def from_json(cls, json_str: str) -> Response:
        """
        Parse Response from JSON string.

        Args:
            json_str: JSON string to parse.

        Returns:
            Response instance.

        Raises:
            ProtocolError: If the JSON is invalid or doesn't match schema.
        """
        logger.debug("Parsing response from JSON")
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as err:
            raise ProtocolError(f"Invalid JSON: {err}", raw_data=json_str) from err

        return cls.from_dict(data)

    @classmethod
    def from_bytes(cls, data: bytes) -> Response:
        """Parse Response from bytes."""
        return cls.from_json(data.decode("utf-8"))

    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.result.status == ResponseStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if response indicates error."""
        return self.result.status == ResponseStatus.ERROR


def create_ping_request() -> Request:
    """Create a ping request for connection health check."""
    logger.debug("Creating ping request")
    return Request(method=MessageMethod.PING)


def create_execute_request(code: str, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> Request:
    """
    Create a code execution request.

    Args:
        code: Python code to execute in Blender.
        timeout_ms: Timeout in milliseconds.

    Returns:
        Request for code execution.
    """
    logger.debug(
        "Creating execute request",
        extra={"code_length": len(code), "timeout_ms": timeout_ms},
    )
    return Request(
        method=MessageMethod.EXECUTE_CODE,
        params=RequestParams(code=code, timeout=timeout_ms),
    )


def create_query_request(query: str) -> Request:
    """
    Create a scene query request.

    Args:
        query: Query string for scene information.

    Returns:
        Request for scene query.
    """
    logger.debug("Creating query request", extra={"query": query})
    return Request(
        method=MessageMethod.QUERY_SCENE,
        params=RequestParams(query=query),
    )


def create_success_response(
    request_id: str,
    data: dict[str, Any] | None = None,
    logs: str = "",
) -> Response:
    """
    Create a success response.

    Args:
        request_id: ID of the original request.
        data: Response data payload.
        logs: Captured logs/output.

    Returns:
        Success response.
    """
    logger.debug("Creating success response", extra={"request_id": request_id})
    return Response(
        id=request_id,
        result=ResponseResult(
            status=ResponseStatus.SUCCESS,
            data=data or {},
            logs=logs,
        ),
    )


def create_error_response(
    request_id: str,
    error: str,
    traceback: str | None = None,
    logs: str = "",
) -> Response:
    """
    Create an error response.

    Args:
        request_id: ID of the original request.
        error: Error message.
        traceback: Full traceback if available.
        logs: Captured logs/output.

    Returns:
        Error response.
    """
    logger.debug(
        "Creating error response",
        extra={"request_id": request_id, "error": error},
    )
    return Response(
        id=request_id,
        result=ResponseResult(
            status=ResponseStatus.ERROR,
            error=error,
            traceback=traceback,
            logs=logs,
        ),
    )
