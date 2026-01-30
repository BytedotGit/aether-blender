"""
Centralized Logging System for Aether-Blender.

This module provides a consistent logging interface across all components.
All modules should use get_logger(__name__) to obtain their logger instance.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON-structured log entries."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON-structured string."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "extra") and record.extra:
            log_entry["context"] = record.extra

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console with colors."""
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Build base message
        message = f"[{timestamp}] [{record.name}] [{color}{record.levelname}{self.RESET}] {record.getMessage()}"

        # Add extra context if present
        if hasattr(record, "extra") and record.extra:
            context_str = json.dumps(record.extra)
            message += f" {context_str}"

        return message


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that handles extra context properly."""

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Process log message to include extra context."""
        extra = kwargs.get("extra", {})
        if self.extra:
            extra = {**self.extra, **extra}
        kwargs["extra"] = extra

        # Store extra in record for formatters
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        return msg, kwargs


# Module-level logger cache
_loggers: dict[str, logging.Logger] = {}
_configured = False


def configure_logging(
    level: str = "DEBUG",
    log_file: str | Path | None = None,
    console: bool = True,
) -> None:
    """
    Configure the logging system.

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, uses default logs/aether.log
        console: Whether to output to console
    """
    global _configured

    # Determine log level from environment or parameter
    env_level = os.environ.get("AETHER_LOG_LEVEL", level).upper()
    log_level = getattr(logging, env_level, logging.DEBUG)

    # Get root logger for aether
    root_logger = logging.getLogger("src")
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(ConsoleFormatter())
        root_logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "aether.log"
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)

    _configured = True

    # Log startup
    root_logger.info(
        "Logging configured",
        extra={"level": env_level, "file": str(log_file)},
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for a module.

    Args:
        name: Module name, typically __name__

    Returns:
        Configured logger instance

    Example:
        from src.telemetry.logger import get_logger

        logger = get_logger(__name__)
        logger.debug("Processing request", extra={"request_id": "123"})
    """
    global _configured

    if not _configured:
        configure_logging()

    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger

    return _loggers[name]
