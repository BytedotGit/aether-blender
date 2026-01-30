"""
Unit Tests for Bridge Protocol Module.

Tests JSON-RPC message validation, serialization, and error handling.
"""

import json

import pytest

from src.bridge.exceptions import ProtocolError
from src.bridge.protocol import (
    DEFAULT_TIMEOUT_MS,
    JSONRPC_VERSION,
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


class TestRequest:
    """Tests for Request class."""

    def test_request_creation_default_values(self) -> None:
        """Test that Request creates with default values."""
        request = Request(method=MessageMethod.PING)

        assert request.jsonrpc == JSONRPC_VERSION
        assert request.method == MessageMethod.PING
        assert request.id is not None
        assert len(request.id) > 0
        assert request.params.timeout == DEFAULT_TIMEOUT_MS

    def test_request_creation_custom_id(self) -> None:
        """Test that Request accepts custom ID."""
        custom_id = "custom-test-id"
        request = Request(method=MessageMethod.PING, id=custom_id)

        assert request.id == custom_id

    def test_request_to_dict_structure(self) -> None:
        """Test that to_dict produces correct structure."""
        request = Request(
            method=MessageMethod.EXECUTE_CODE,
            params=RequestParams(code="print('hello')", timeout=1000),
            id="test-id",
        )

        result = request.to_dict()

        assert result["jsonrpc"] == JSONRPC_VERSION
        assert result["id"] == "test-id"
        assert result["method"] == "execute_code"
        assert result["params"]["code"] == "print('hello')"
        assert result["params"]["timeout"] == 1000

    def test_request_to_json_valid(self) -> None:
        """Test that to_json produces valid JSON."""
        request = Request(method=MessageMethod.PING, id="test-id")

        json_str = request.to_json()
        parsed = json.loads(json_str)

        assert parsed["jsonrpc"] == JSONRPC_VERSION
        assert parsed["id"] == "test-id"
        assert parsed["method"] == "ping"

    def test_request_to_bytes_utf8(self) -> None:
        """Test that to_bytes produces UTF-8 encoded bytes."""
        request = Request(method=MessageMethod.PING, id="test-id")

        data = request.to_bytes()

        assert isinstance(data, bytes)
        decoded = data.decode("utf-8")
        parsed = json.loads(decoded)
        assert parsed["method"] == "ping"

    def test_request_from_dict_valid(self) -> None:
        """Test parsing Request from valid dictionary."""
        data = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "execute_code",
            "params": {"code": "x = 1", "timeout": 2000},
        }

        request = Request.from_dict(data)

        assert request.id == "test-id"
        assert request.method == MessageMethod.EXECUTE_CODE
        assert request.params.code == "x = 1"
        assert request.params.timeout == 2000

    def test_request_from_dict_missing_jsonrpc(self) -> None:
        """Test that missing jsonrpc raises ProtocolError."""
        data = {"id": "test-id", "method": "ping"}

        with pytest.raises(ProtocolError) as exc_info:
            Request.from_dict(data)

        assert "Invalid jsonrpc version" in str(exc_info.value)

    def test_request_from_dict_wrong_jsonrpc_version(self) -> None:
        """Test that wrong jsonrpc version raises ProtocolError."""
        data = {"jsonrpc": "1.0", "id": "test-id", "method": "ping"}

        with pytest.raises(ProtocolError) as exc_info:
            Request.from_dict(data)

        assert "Invalid jsonrpc version" in str(exc_info.value)

    def test_request_from_dict_missing_method(self) -> None:
        """Test that missing method raises ProtocolError."""
        data = {"jsonrpc": "2.0", "id": "test-id"}

        with pytest.raises(ProtocolError) as exc_info:
            Request.from_dict(data)

        assert "Missing required field: method" in str(exc_info.value)

    def test_request_from_dict_missing_id(self) -> None:
        """Test that missing id raises ProtocolError."""
        data = {"jsonrpc": "2.0", "method": "ping"}

        with pytest.raises(ProtocolError) as exc_info:
            Request.from_dict(data)

        assert "Missing required field: id" in str(exc_info.value)

    def test_request_from_dict_unknown_method(self) -> None:
        """Test that unknown method raises ProtocolError."""
        data = {"jsonrpc": "2.0", "id": "test-id", "method": "unknown_method"}

        with pytest.raises(ProtocolError) as exc_info:
            Request.from_dict(data)

        assert "Unknown method" in str(exc_info.value)

    def test_request_from_json_valid(self) -> None:
        """Test parsing Request from valid JSON string."""
        json_str = '{"jsonrpc": "2.0", "id": "test-id", "method": "ping", "params": {}}'

        request = Request.from_json(json_str)

        assert request.id == "test-id"
        assert request.method == MessageMethod.PING

    def test_request_from_json_invalid_json(self) -> None:
        """Test that invalid JSON raises ProtocolError."""
        with pytest.raises(ProtocolError) as exc_info:
            Request.from_json("not valid json")

        assert "Invalid JSON" in str(exc_info.value)

    def test_request_from_bytes_valid(self) -> None:
        """Test parsing Request from bytes."""
        json_bytes = b'{"jsonrpc": "2.0", "id": "test-id", "method": "ping"}'

        request = Request.from_bytes(json_bytes)

        assert request.id == "test-id"
        assert request.method == MessageMethod.PING

    def test_request_roundtrip(self) -> None:
        """Test that Request survives serialization roundtrip."""
        original = Request(
            method=MessageMethod.EXECUTE_CODE,
            params=RequestParams(code="print(1)", timeout=3000),
            id="roundtrip-id",
        )

        json_str = original.to_json()
        restored = Request.from_json(json_str)

        assert restored.id == original.id
        assert restored.method == original.method
        assert restored.params.code == original.params.code
        assert restored.params.timeout == original.params.timeout


class TestResponse:
    """Tests for Response class."""

    def test_response_creation(self) -> None:
        """Test basic Response creation."""
        response = Response(
            id="test-id",
            result=ResponseResult(
                status=ResponseStatus.SUCCESS,
                data={"key": "value"},
                logs="some output",
            ),
        )

        assert response.id == "test-id"
        assert response.jsonrpc == JSONRPC_VERSION
        assert response.result.status == ResponseStatus.SUCCESS
        assert response.result.data == {"key": "value"}
        assert response.result.logs == "some output"

    def test_response_is_success(self) -> None:
        """Test is_success property."""
        success_response = Response(
            id="test-id",
            result=ResponseResult(status=ResponseStatus.SUCCESS),
        )
        error_response = Response(
            id="test-id",
            result=ResponseResult(status=ResponseStatus.ERROR, error="failed"),
        )

        assert success_response.is_success is True
        assert success_response.is_error is False
        assert error_response.is_success is False
        assert error_response.is_error is True

    def test_response_to_dict_success(self) -> None:
        """Test to_dict for success response."""
        response = Response(
            id="test-id",
            result=ResponseResult(
                status=ResponseStatus.SUCCESS,
                data={"count": 5},
                logs="done",
            ),
        )

        result = response.to_dict()

        assert result["jsonrpc"] == JSONRPC_VERSION
        assert result["id"] == "test-id"
        assert result["result"]["status"] == "success"
        assert result["result"]["data"] == {"count": 5}
        assert result["result"]["logs"] == "done"

    def test_response_to_dict_error(self) -> None:
        """Test to_dict for error response."""
        response = Response(
            id="test-id",
            result=ResponseResult(
                status=ResponseStatus.ERROR,
                error="Something went wrong",
                traceback="Traceback...",
            ),
        )

        result = response.to_dict()

        assert result["result"]["status"] == "error"
        assert result["result"]["error"] == "Something went wrong"
        assert result["result"]["traceback"] == "Traceback..."

    def test_response_to_json_valid(self) -> None:
        """Test that to_json produces valid JSON."""
        response = Response(
            id="test-id",
            result=ResponseResult(status=ResponseStatus.SUCCESS),
        )

        json_str = response.to_json()
        parsed = json.loads(json_str)

        assert parsed["id"] == "test-id"
        assert parsed["result"]["status"] == "success"

    def test_response_from_dict_valid_success(self) -> None:
        """Test parsing success Response from dictionary."""
        data = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {
                "status": "success",
                "data": {"items": [1, 2, 3]},
                "logs": "processed",
            },
        }

        response = Response.from_dict(data)

        assert response.id == "test-id"
        assert response.is_success is True
        assert response.result.data == {"items": [1, 2, 3]}
        assert response.result.logs == "processed"

    def test_response_from_dict_valid_error(self) -> None:
        """Test parsing error Response from dictionary."""
        data = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {
                "status": "error",
                "error": "Failed to execute",
                "traceback": "line 1: error",
            },
        }

        response = Response.from_dict(data)

        assert response.id == "test-id"
        assert response.is_error is True
        assert response.result.error == "Failed to execute"
        assert response.result.traceback == "line 1: error"

    def test_response_from_dict_missing_result(self) -> None:
        """Test that missing result raises ProtocolError."""
        data = {"jsonrpc": "2.0", "id": "test-id"}

        with pytest.raises(ProtocolError) as exc_info:
            Response.from_dict(data)

        assert "Missing required field: result" in str(exc_info.value)

    def test_response_from_json_invalid(self) -> None:
        """Test that invalid JSON raises ProtocolError."""
        with pytest.raises(ProtocolError):
            Response.from_json("invalid json{")

    def test_response_roundtrip(self) -> None:
        """Test that Response survives serialization roundtrip."""
        original = Response(
            id="roundtrip-id",
            result=ResponseResult(
                status=ResponseStatus.SUCCESS,
                data={"nested": {"key": "value"}},
                logs="output text",
            ),
        )

        json_str = original.to_json()
        restored = Response.from_json(json_str)

        assert restored.id == original.id
        assert restored.result.status == original.result.status
        assert restored.result.data == original.result.data
        assert restored.result.logs == original.result.logs


class TestMessageMethod:
    """Tests for MessageMethod enum."""

    def test_all_methods_exist(self) -> None:
        """Test that all expected methods are defined."""
        assert MessageMethod.PING.value == "ping"
        assert MessageMethod.EXECUTE_CODE.value == "execute_code"
        assert MessageMethod.QUERY_SCENE.value == "query_scene"
        assert MessageMethod.GET_OBJECTS.value == "get_objects"
        assert MessageMethod.SHUTDOWN.value == "shutdown"

    def test_method_values_are_strings(self) -> None:
        """Test that method values are strings."""
        for method in MessageMethod:
            assert isinstance(method.value, str)


class TestFactoryFunctions:
    """Tests for protocol factory functions."""

    def test_create_ping_request(self) -> None:
        """Test create_ping_request factory."""
        request = create_ping_request()

        assert request.method == MessageMethod.PING
        assert request.id is not None

    def test_create_execute_request(self) -> None:
        """Test create_execute_request factory."""
        code = "bpy.ops.mesh.primitive_cube_add()"
        request = create_execute_request(code, timeout_ms=10000)

        assert request.method == MessageMethod.EXECUTE_CODE
        assert request.params.code == code
        assert request.params.timeout == 10000

    def test_create_execute_request_default_timeout(self) -> None:
        """Test create_execute_request uses default timeout."""
        request = create_execute_request("x = 1")

        assert request.params.timeout == DEFAULT_TIMEOUT_MS

    def test_create_query_request(self) -> None:
        """Test create_query_request factory."""
        request = create_query_request("objects")

        assert request.method == MessageMethod.QUERY_SCENE
        assert request.params.query == "objects"

    def test_create_success_response(self) -> None:
        """Test create_success_response factory."""
        response = create_success_response(
            request_id="test-id",
            data={"result": True},
            logs="operation complete",
        )

        assert response.id == "test-id"
        assert response.is_success is True
        assert response.result.data == {"result": True}
        assert response.result.logs == "operation complete"

    def test_create_success_response_defaults(self) -> None:
        """Test create_success_response with defaults."""
        response = create_success_response(request_id="test-id")

        assert response.result.data == {}
        assert response.result.logs == ""

    def test_create_error_response(self) -> None:
        """Test create_error_response factory."""
        response = create_error_response(
            request_id="test-id",
            error="Something failed",
            traceback="line 5: error",
            logs="partial output",
        )

        assert response.id == "test-id"
        assert response.is_error is True
        assert response.result.error == "Something failed"
        assert response.result.traceback == "line 5: error"
        assert response.result.logs == "partial output"

    def test_create_error_response_minimal(self) -> None:
        """Test create_error_response with minimal args."""
        response = create_error_response(request_id="test-id", error="failed")

        assert response.is_error is True
        assert response.result.error == "failed"
        assert response.result.traceback is None
        assert response.result.logs == ""


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_params(self) -> None:
        """Test Request with no params specified."""
        data = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "ping",
        }

        request = Request.from_dict(data)

        assert request.params.code is None
        assert request.params.timeout == DEFAULT_TIMEOUT_MS

    def test_unicode_in_code(self) -> None:
        """Test handling of unicode characters in code."""
        code = "print('こんにちは世界 🌍')"
        request = create_execute_request(code)

        json_str = request.to_json()
        restored = Request.from_json(json_str)

        assert restored.params.code == code

    def test_large_data_in_response(self) -> None:
        """Test Response with large data payload."""
        large_list = list(range(1000))
        response = create_success_response(
            request_id="test-id",
            data={"items": large_list},
        )

        json_str = response.to_json()
        restored = Response.from_json(json_str)

        assert restored.result.data["items"] == large_list

    def test_special_characters_in_error(self) -> None:
        """Test special characters in error messages."""
        error_msg = "Error: \"quoted\" and 'single' with\nnewlines"
        response = create_error_response(request_id="test-id", error=error_msg)

        json_str = response.to_json()
        restored = Response.from_json(json_str)

        assert restored.result.error == error_msg
