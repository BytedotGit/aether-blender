# AGENTS.md - Telemetry Module

## Purpose

Centralized logging and monitoring for the entire application. **This module is MANDATORY for all other modules.**

---

## MANDATORY: Every Module Uses Telemetry

### The Observability Rule

**Every function in every module MUST use the telemetry system.** No exceptions.

### Quick Start

```python
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

def my_function(param: str) -> bool:
    """Function with proper observability."""
    logger.debug("Entering my_function", extra={"param": param})

    try:
        result = do_work()
        logger.debug("Exiting my_function", extra={"result": result})
        return result
    except Exception as e:
        logger.error("Error in my_function", extra={"error": str(e)})
        raise
```

---

## Files

| File           | Purpose                        | Max Lines |
| -------------- | ------------------------------ | --------- |
| `__init__.py`  | Public exports                 | 20        |
| `logger.py`    | Logger factory and config      | 200       |
| `formatters.py`| Custom log formatters (future) | 100       |
| `handlers.py`  | File and console handlers (future) | 150   |

## Public API

### `get_logger(name: str) -> logging.Logger`

Get a configured logger for a module. Always pass `__name__`.

```python
from src.telemetry.logger import get_logger

logger = get_logger(__name__)  # e.g., "src.bridge.client"
```

### `configure_logging(level: str, log_file: Path, console: bool)`

Configure global logging settings. Called once at application startup.

```python
from src.telemetry.logger import configure_logging

configure_logging(level="DEBUG", console=True)
```

---

## Logging Patterns

### Pattern 1: Function Entry/Exit

```python
def process_data(data: list[str]) -> dict:
    logger.debug("Entering process_data", extra={"data_count": len(data)})

    result = {"processed": len(data)}

    logger.debug("Exiting process_data", extra={"result": result})
    return result
```

### Pattern 2: Error Handling with Context

```python
def connect_to_server(host: str, port: int) -> Connection:
    logger.info("Connecting to server", extra={"host": host, "port": port})

    try:
        conn = Connection(host, port)
        conn.open()
        logger.info("Connected successfully", extra={"host": host})
        return conn
    except TimeoutError as e:
        logger.error(
            "Connection timeout",
            extra={"host": host, "port": port, "error": str(e)}
        )
        raise
    except ConnectionRefusedError as e:
        logger.error(
            "Connection refused",
            extra={"host": host, "port": port, "error": str(e)}
        )
        raise
```

### Pattern 3: Performance Tracking

```python
import time

def expensive_operation(items: list) -> list:
    start = time.perf_counter()
    logger.debug("Starting expensive_operation", extra={"item_count": len(items)})

    result = [process(item) for item in items]

    elapsed = time.perf_counter() - start
    logger.info(
        "Completed expensive_operation",
        extra={"item_count": len(items), "elapsed_seconds": round(elapsed, 3)}
    )
    return result
```

### Pattern 4: Loop Progress

```python
def batch_process(items: list) -> None:
    total = len(items)
    logger.info("Starting batch process", extra={"total": total})

    for i, item in enumerate(items):
        if i % 100 == 0:  # Log every 100 items
            logger.debug("Batch progress", extra={"processed": i, "total": total})
        process(item)

    logger.info("Batch process complete", extra={"processed": total})
```

---

## Log Levels - When to Use

| Level | When | Example |
|-------|------|---------|
| `DEBUG` | Function entry/exit, variable values, loop iterations | "Entering connect()", "Attempt 3 of 5" |
| `INFO` | Significant operations, milestones, user-facing events | "Connection established", "File saved" |
| `WARNING` | Recoverable issues, deprecations, fallbacks | "Retry attempted", "Using default config" |
| `ERROR` | Failures that need attention but don't crash | "API call failed", "Invalid response" |
| `CRITICAL` | System-breaking failures, unrecoverable states | "Database unreachable", "Config file missing" |

---

## Log Format

Console output:
```text
[2026-01-30 14:30:00] [src.bridge.client] [INFO] Message {"key": "value"}
```

JSON format (for log files):
```json
{
  "timestamp": "2026-01-30T14:30:00.123456",
  "level": "INFO",
  "logger": "src.bridge.client",
  "message": "Connection established",
  "context": {"host": "localhost", "port": 5005}
}
```

---

## Context Data Best Practices

### Always Include:
- Function parameters (sanitized if sensitive)
- Return values or result summaries
- Error details and types
- Timing information for slow operations

### Never Include:
- Passwords or API keys
- Personal user data
- Large data dumps (use summaries)

### Example - Good Context:

```python
# GOOD - Useful context
logger.error(
    "Failed to execute code",
    extra={
        "code_length": len(code),
        "error_type": type(e).__name__,
        "error_message": str(e),
        "line_number": getattr(e, "lineno", None),
        "attempt": retry_count
    }
)
```

```python
# BAD - Not enough context
logger.error("Error occurred")  # Useless!
```

---

## Log Files

| File | Purpose |
|------|---------|
| `logs/aether.log` | Main application log |
| `logs/blender_execution.log` | Blender-side execution log |

- Files are NOT rotated (per user preference)
- Git-ignored via `.gitignore`

## Verbosity Control

- Environment variable: `AETHER_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR`
- Default: `DEBUG` in development
- Configurable at runtime

---

## Testing Logging

When testing, verify logging behavior:

```python
from unittest.mock import patch

def test_function_logs_entry_and_exit():
    with patch("src.module.logger") as mock_logger:
        my_function("test")

        # Verify entry log
        mock_logger.debug.assert_any_call(
            "Entering my_function",
            extra={"param": "test"}
        )
```
        raise
```

## JSON Context

Use `extra` parameter for structured data:

```python
logger.info("User request", extra={
    "user_id": user_id,
    "request": request_text,
    "timestamp": datetime.now().isoformat()
})
```
