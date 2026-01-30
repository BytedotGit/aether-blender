# AGENTS.md - Telemetry Module

## Purpose

Centralized logging and monitoring for the entire application.

## Files

| File           | Purpose                        | Max Lines |
| -------------- | ------------------------------ | --------- |
| `__init__.py`  | Public exports                 | 20        |
| `logger.py`    | Logger factory and config      | 200       |
| `formatters.py`| Custom log formatters          | 100       |
| `handlers.py`  | File and console handlers      | 150       |

## Logger Factory

```python
import logging
from pathlib import Path

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for a module."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        configure_logger(logger)
    return logger
```

## Log Format

```text
[2026-01-30 14:30:00.123] [module.name] [LEVEL] Message {"key": "value"}
```

## Log Levels Configuration

```python
LEVELS = {
    "DEBUG": logging.DEBUG,      # Function entry/exit, variables
    "INFO": logging.INFO,        # Significant operations
    "WARNING": logging.WARNING,  # Recoverable issues
    "ERROR": logging.ERROR,      # Failures
    "CRITICAL": logging.CRITICAL # System-breaking
}
```

## Verbosity Control

- Environment variable: `AETHER_LOG_LEVEL`
- Default: `DEBUG` in development, `INFO` in production
- Configurable per-module

## Log Files

- Main log: `logs/aether.log`
- Blender log: `logs/blender_execution.log`
- No rotation (logs grow indefinitely per user request)
- Git-ignored via `.gitignore`

## Cross-Process Logging

The Blender addon writes to: `logs/blender_execution.log`
The main application reads this file for error propagation.

## Usage Pattern

```python
from src.telemetry.logger import get_logger

logger = get_logger(__name__)

def my_function(param: str) -> bool:
    logger.debug("Entering my_function", extra={"param": param})
    try:
        result = do_something()
        logger.info("Operation completed", extra={"result": result})
        return result
    except SomeError as e:
        logger.error("Operation failed", extra={"error": str(e)})
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
