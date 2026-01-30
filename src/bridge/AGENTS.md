# AGENTS.md - Bridge Module

## Purpose

Handles Inter-Process Communication (IPC) between the external Python environment (Poetry/VS Code) and Blender's internal Python environment.

## Architecture

```text
┌─────────────────────┐         TCP Socket        ┌─────────────────────┐
│   BlenderClient     │ ◄─────────────────────►  │   Blender Addon     │
│   (this module)     │        Port 5005         │   (blender_addon/)  │
└─────────────────────┘                           └─────────────────────┘
```

## Files

| File            | Purpose                              | Max Lines |
| --------------- | ------------------------------------ | --------- |
| `client.py`     | Socket client for connecting         | 300       |
| `protocol.py`   | JSON-RPC message schema/validation   | 200       |
| `exceptions.py` | Custom exceptions for bridge errors  | 100       |
| `connection.py` | Connection lifecycle management      | 250       |

## Protocol Schema

### Request

```json
{
  "jsonrpc": "2.0",
  "id": "uuid-v4",
  "method": "execute_code | ping | query_scene",
  "params": {
    "code": "string (for execute_code)",
    "timeout": 5000
  }
}
```

### Response

```json
{
  "jsonrpc": "2.0",
  "id": "uuid-v4 (matching request)",
  "result": {
    "status": "success | error",
    "data": {},
    "logs": "captured stdout",
    "error": "traceback if failed"
  }
}
```

## Critical Constraints

1. **Timeout Handling:** All socket operations must have timeouts
2. **Reconnection:** Must handle Blender restart gracefully
3. **Message Framing:** Use 4-byte length prefix to prevent fragmentation
4. **Thread Safety:** Client may be called from multiple threads

## Error Handling

```python
class BridgeError(AetherError):
    """Base for bridge errors."""
    pass

class ConnectionRefusedError(BridgeError):
    """Blender is not running or addon not active."""
    pass

class ConnectionTimeoutError(BridgeError):
    """Blender did not respond in time."""
    pass

class ProtocolError(BridgeError):
    """Invalid message format."""
    pass
```

## Testing Requirements

- Test connection to running Blender
- Test timeout behavior
- Test reconnection after disconnect
- Test message framing with large payloads
- Test concurrent requests
