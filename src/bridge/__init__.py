"""Bridge module __init__.py - Inter-Process Communication."""

from src.bridge.client import BlenderClient
from src.bridge.exceptions import (
    AetherError,
    BridgeError,
    ConnectionClosedError,
    ConnectionRefusedError,
    ConnectionTimeoutError,
    ExecutionError,
    MessageFramingError,
    ProtocolError,
)
from src.bridge.protocol import (
    MessageMethod,
    Request,
    RequestParams,
    Response,
    ResponseResult,
    ResponseStatus,
    create_error_response,
    create_execute_request,
    create_ping_request,
    create_query_request,
    create_success_response,
)

__all__ = [
    # Client
    "BlenderClient",
    # Exceptions
    "AetherError",
    "BridgeError",
    "ConnectionClosedError",
    "ConnectionRefusedError",
    "ConnectionTimeoutError",
    "ExecutionError",
    "MessageFramingError",
    "ProtocolError",
    # Protocol
    "MessageMethod",
    "Request",
    "RequestParams",
    "Response",
    "ResponseResult",
    "ResponseStatus",
    "create_error_response",
    "create_execute_request",
    "create_ping_request",
    "create_query_request",
    "create_success_response",
]
