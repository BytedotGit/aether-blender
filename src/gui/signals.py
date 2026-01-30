"""
Aether GUI Signals Module.

Centralized Qt signals for cross-component communication.
All inter-panel and orchestrator communication flows through these signals.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from src.telemetry.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Enums for Signal Data
# ============================================================================


class MessageRole(Enum):
    """Role of a chat message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


class ConnectionState(Enum):
    """Blender connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class ToastLevel(Enum):
    """Toast notification severity level."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


# ============================================================================
# Data Classes for Signal Payloads
# ============================================================================


@dataclass
class ChatMessage:
    """Represents a chat message."""

    role: MessageRole
    content: str
    timestamp: datetime
    code: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ExecutionResult:
    """Result of code execution in Blender."""

    success: bool
    code: str
    output: str | None = None
    error: str | None = None
    execution_time: float = 0.0
    attempts: int = 1


@dataclass
class ToastNotification:
    """Toast notification data."""

    message: str
    level: ToastLevel = ToastLevel.INFO
    duration_ms: int = 3000
    title: str | None = None


# ============================================================================
# Central Signal Hub
# ============================================================================


class AetherSignals(QObject):
    """
    Central signal hub for Aether GUI application.

    All cross-component communication flows through these signals.
    Components connect to signals they need and emit signals to communicate.

    Usage:
        signals = AetherSignals()

        # Connect to signals
        signals.message_received.connect(self.on_message)

        # Emit signals
        signals.message_received.emit(ChatMessage(...))
    """

    # ========================================================================
    # Chat Signals
    # ========================================================================

    # Emitted when user submits a new message
    user_message_submitted = pyqtSignal(str)

    # Emitted when a chat message is received (from AI or system)
    message_received = pyqtSignal(object)  # ChatMessage

    # Emitted when chat history should be cleared
    chat_cleared = pyqtSignal()

    # Emitted when processing starts/stops (for UI state)
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal()

    # ========================================================================
    # Blender Connection Signals
    # ========================================================================

    # Emitted when connection state changes
    connection_state_changed = pyqtSignal(object)  # ConnectionState

    # Emitted when Blender connection is established
    blender_connected = pyqtSignal()

    # Emitted when Blender connection is lost
    blender_disconnected = pyqtSignal()

    # Emitted to request a connection attempt
    connection_requested = pyqtSignal()

    # Emitted to request disconnection
    disconnection_requested = pyqtSignal()

    # ========================================================================
    # Execution Signals
    # ========================================================================

    # Emitted when code execution completes
    execution_complete = pyqtSignal(object)  # ExecutionResult

    # Emitted when code is about to be executed (for preview)
    code_preview_requested = pyqtSignal(str)

    # Emitted when execution fails
    execution_failed = pyqtSignal(str, str)  # code, error

    # ========================================================================
    # Notification Signals
    # ========================================================================

    # Emitted to show a toast notification
    toast_requested = pyqtSignal(object)  # ToastNotification

    # Convenience methods will emit this with proper ToastNotification

    # Emitted when a critical error occurs
    error_occurred = pyqtSignal(str)

    # ========================================================================
    # Settings Signals
    # ========================================================================

    # Emitted when settings are changed
    settings_changed = pyqtSignal(dict)

    # Emitted when AI provider changes
    provider_changed = pyqtSignal(str, str)  # provider_name, model_name

    # ========================================================================
    # Application Signals
    # ========================================================================

    # Emitted when application should quit
    quit_requested = pyqtSignal()

    # Emitted when application is ready
    app_ready = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize signals hub."""
        super().__init__(parent)
        logger.debug("AetherSignals initialized")

    # ========================================================================
    # Convenience Methods
    # ========================================================================

    def show_toast(
        self,
        message: str,
        level: ToastLevel = ToastLevel.INFO,
        duration_ms: int = 3000,
        title: str | None = None,
    ) -> None:
        """Emit a toast notification request."""
        logger.debug(
            "Toast requested",
            extra={"toast_message": message, "level": level.value},
        )
        notification = ToastNotification(
            message=message,
            level=level,
            duration_ms=duration_ms,
            title=title,
        )
        self.toast_requested.emit(notification)

    def show_success(self, message: str, duration_ms: int = 3000) -> None:
        """Show a success toast."""
        self.show_toast(message, ToastLevel.SUCCESS, duration_ms)

    def show_error(self, message: str, duration_ms: int = 5000) -> None:
        """Show an error toast."""
        self.show_toast(message, ToastLevel.ERROR, duration_ms)

    def show_warning(self, message: str, duration_ms: int = 4000) -> None:
        """Show a warning toast."""
        self.show_toast(message, ToastLevel.WARNING, duration_ms)

    def show_info(self, message: str, duration_ms: int = 3000) -> None:
        """Show an info toast."""
        self.show_toast(message, ToastLevel.INFO, duration_ms)

    def send_message(
        self, role: MessageRole, content: str, code: str | None = None
    ) -> None:
        """Emit a chat message received signal."""
        logger.debug(
            "Sending message",
            extra={"role": role.value, "content_length": len(content)},
        )
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            code=code,
        )
        self.message_received.emit(message)


# ============================================================================
# Singleton Instance
# ============================================================================

# Global signals instance for application-wide access
_signals_instance: AetherSignals | None = None


def get_signals() -> AetherSignals:
    """Get the global signals instance (lazy initialization)."""
    global _signals_instance
    if _signals_instance is None:
        _signals_instance = AetherSignals()
        logger.info("Global AetherSignals instance created")
    return _signals_instance


def reset_signals() -> None:
    """Reset the global signals instance (for testing)."""
    global _signals_instance
    logger.debug("Resetting global AetherSignals instance")
    _signals_instance = None
