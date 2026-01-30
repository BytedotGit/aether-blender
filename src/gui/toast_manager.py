"""Toast notification manager for Aether GUI.

This module provides a toast notification system that displays temporary
messages to the user. Toasts can be success, error, warning, or info
messages and automatically dismiss after a configurable duration.
"""

from dataclasses import dataclass
from typing import Optional

from PyQt6.QtCore import QPropertyAnimation, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from src.gui.signals import ToastLevel, ToastNotification, get_signals
from src.gui.styles import COLORS, DIMS, FONTS
from src.telemetry.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ToastConfig:
    """Configuration for toast display behavior."""

    default_duration_ms: int = 4000
    fade_duration_ms: int = 300
    max_visible: int = 5
    spacing: int = 10
    margin_right: int = 20
    margin_bottom: int = 20


class ToastWidget(QWidget):
    """Individual toast notification widget.

    A toast displays a message with an icon indicating the level
    (success, error, warning, info) and automatically fades out
    after the specified duration.
    """

    # Level to icon mapping (Unicode characters)
    LEVEL_ICONS = {
        ToastLevel.SUCCESS: "✓",
        ToastLevel.ERROR: "✕",
        ToastLevel.WARNING: "⚠",
        ToastLevel.INFO: "ℹ",
    }

    # Level to color mapping
    LEVEL_COLORS = {
        ToastLevel.SUCCESS: COLORS.success,
        ToastLevel.ERROR: COLORS.error,
        ToastLevel.WARNING: COLORS.warning,
        ToastLevel.INFO: COLORS.primary,
    }

    def __init__(
        self,
        notification: ToastNotification,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize toast widget.

        Args:
            notification: The toast notification data
            parent: Parent widget
        """
        logger.debug(
            "Entering ToastWidget.__init__",
            extra={
                "level": notification.level.value,
                "toast_msg": notification.message,
            },
        )
        super().__init__(parent)
        self._notification = notification
        self._setup_ui()
        self._apply_styles()

        logger.debug("Exiting ToastWidget.__init__")

    def _setup_ui(self) -> None:
        """Set up the toast UI components."""
        logger.debug("Entering ToastWidget._setup_ui")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Container for content
        self._container = QWidget()
        self._container.setObjectName("toast_container")
        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(4)

        # Title with icon
        icon = self.LEVEL_ICONS.get(self._notification.level, "ℹ")
        title = self._notification.title or self._notification.level.value.capitalize()
        self._title_label = QLabel(f"{icon} {title}")
        self._title_label.setObjectName("toast_title")
        container_layout.addWidget(self._title_label)

        # Message
        self._message_label = QLabel(self._notification.message)
        self._message_label.setObjectName("toast_message")
        self._message_label.setWordWrap(True)
        self._message_label.setMaximumWidth(300)
        container_layout.addWidget(self._message_label)

        layout.addWidget(self._container)

        # Size hint
        self.adjustSize()
        self.setMinimumWidth(200)
        self.setMaximumWidth(350)

        logger.debug("Exiting ToastWidget._setup_ui")

    def _apply_styles(self) -> None:
        """Apply styles based on notification level."""
        logger.debug("Entering ToastWidget._apply_styles")

        color = self.LEVEL_COLORS.get(self._notification.level, COLORS.primary)

        stylesheet = f"""
            #toast_container {{
                background-color: {COLORS.bg_medium};
                border: 2px solid {color};
                border-radius: {DIMS.radius_md}px;
            }}
            #toast_title {{
                color: {color};
                font-family: {FONTS.family_default};
                font-size: {FONTS.size_normal}px;
                font-weight: bold;
            }}
            #toast_message {{
                color: {COLORS.text_secondary};
                font-family: {FONTS.family_default};
                font-size: {FONTS.size_small}px;
            }}
        """
        self.setStyleSheet(stylesheet)

        logger.debug("Exiting ToastWidget._apply_styles")

    @property
    def notification(self) -> ToastNotification:
        """Get the notification data."""
        return self._notification


class ToastManager(QWidget):
    """Manager for displaying and stacking toast notifications.

    The ToastManager handles the display, positioning, and lifecycle
    of toast notifications. It ensures toasts are stacked properly
    and handles automatic dismissal with fade animations.
    """

    _instance: Optional["ToastManager"] = None

    def __init__(
        self,
        config: ToastConfig | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize toast manager.

        Args:
            config: Toast configuration options
            parent: Parent widget
        """
        logger.debug("Entering ToastManager.__init__")
        super().__init__(parent)
        self._config = config or ToastConfig()
        self._active_toasts: list[ToastWidget] = []
        self._pending_toasts: list[ToastNotification] = []
        self._animations: dict[ToastWidget, QPropertyAnimation] = {}

        # Connect to signals
        signals = get_signals()
        signals.toast_requested.connect(self._on_toast_requested)

        logger.debug("Exiting ToastManager.__init__")

    @classmethod
    def instance(cls) -> "ToastManager":
        """Get or create the singleton instance.

        Returns:
            The ToastManager singleton instance
        """
        logger.debug("Entering ToastManager.instance")
        if cls._instance is None:
            cls._instance = ToastManager()
        logger.debug("Exiting ToastManager.instance")
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        logger.debug("Entering ToastManager.reset_instance")
        if cls._instance is not None:
            cls._instance.clear_all()
            cls._instance = None
        logger.debug("Exiting ToastManager.reset_instance")

    def _on_toast_requested(self, notification: ToastNotification) -> None:
        """Handle toast request signal.

        Args:
            notification: The toast notification to display
        """
        logger.debug(
            "Entering ToastManager._on_toast_requested",
            extra={"level": notification.level.value},
        )
        self.show_toast(notification)
        logger.debug("Exiting ToastManager._on_toast_requested")

    def show_toast(self, notification: ToastNotification) -> ToastWidget:
        """Display a toast notification.

        Args:
            notification: The toast notification to display

        Returns:
            The created ToastWidget
        """
        logger.debug(
            "Entering ToastManager.show_toast",
            extra={
                "level": notification.level.value,
                "toast_msg": notification.message,
                "active_count": len(self._active_toasts),
            },
        )

        # Check if we're at max capacity
        if len(self._active_toasts) >= self._config.max_visible:
            logger.debug("Max toasts reached, queueing notification")
            self._pending_toasts.append(notification)
            return self._active_toasts[-1]  # Return most recent

        # Create toast widget
        toast = ToastWidget(notification)
        self._active_toasts.append(toast)

        # Position the toast
        self._position_toasts()

        # Show the toast
        toast.show()

        # Set up auto-dismiss timer
        duration = notification.duration_ms or self._config.default_duration_ms
        QTimer.singleShot(duration, lambda: self._dismiss_toast(toast))

        logger.info(
            "Toast displayed",
            extra={
                "level": notification.level.value,
                "duration_ms": duration,
            },
        )
        logger.debug("Exiting ToastManager.show_toast")
        return toast

    def _position_toasts(self) -> None:
        """Position all active toasts in a stack from bottom-right."""
        logger.debug(
            "Entering ToastManager._position_toasts",
            extra={"count": len(self._active_toasts)},
        )

        # Get screen geometry
        screen = QApplication.primaryScreen()
        if screen is None:
            logger.warning("No primary screen found")
            return

        screen_geometry = screen.availableGeometry()
        bottom = screen_geometry.bottom() - self._config.margin_bottom
        right = screen_geometry.right() - self._config.margin_right

        # Position each toast from bottom up
        current_y = bottom
        for toast in reversed(self._active_toasts):
            toast.adjustSize()
            toast_height = toast.height()
            toast_width = toast.width()

            x = right - toast_width
            y = current_y - toast_height

            toast.move(x, y)
            current_y = y - self._config.spacing

        logger.debug("Exiting ToastManager._position_toasts")

    def _dismiss_toast(self, toast: ToastWidget) -> None:
        """Dismiss a toast with fade animation.

        Args:
            toast: The toast widget to dismiss
        """
        logger.debug("Entering ToastManager._dismiss_toast")

        if toast not in self._active_toasts:
            logger.debug("Toast already dismissed")
            return

        # Create fade animation
        animation = QPropertyAnimation(toast, b"windowOpacity")
        animation.setDuration(self._config.fade_duration_ms)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)

        # Clean up when animation finishes
        animation.finished.connect(lambda: self._on_fade_finished(toast))

        self._animations[toast] = animation
        animation.start()

        logger.debug("Exiting ToastManager._dismiss_toast")

    def _on_fade_finished(self, toast: ToastWidget) -> None:
        """Handle fade animation completion.

        Args:
            toast: The toast that finished fading
        """
        logger.debug("Entering ToastManager._on_fade_finished")

        # Remove from active list
        if toast in self._active_toasts:
            self._active_toasts.remove(toast)

        # Clean up animation
        if toast in self._animations:
            del self._animations[toast]

        # Close the widget
        toast.close()
        toast.deleteLater()

        # Reposition remaining toasts
        self._position_toasts()

        # Show pending toasts if any
        if self._pending_toasts:
            next_notification = self._pending_toasts.pop(0)
            self.show_toast(next_notification)

        logger.debug(
            "Exiting ToastManager._on_fade_finished",
            extra={"remaining": len(self._active_toasts)},
        )

    def dismiss_all(self) -> None:
        """Dismiss all active toasts immediately."""
        logger.debug(
            "Entering ToastManager.dismiss_all",
            extra={"count": len(self._active_toasts)},
        )

        # Copy list to avoid modification during iteration
        toasts_to_dismiss = self._active_toasts.copy()
        for toast in toasts_to_dismiss:
            self._dismiss_toast(toast)

        logger.debug("Exiting ToastManager.dismiss_all")

    def clear_all(self) -> None:
        """Clear all toasts immediately without animation."""
        logger.debug("Entering ToastManager.clear_all")

        # Stop all animations
        for animation in self._animations.values():
            animation.stop()
        self._animations.clear()

        # Close all toasts
        for toast in self._active_toasts:
            toast.close()
            toast.deleteLater()
        self._active_toasts.clear()

        # Clear pending
        self._pending_toasts.clear()

        logger.debug("Exiting ToastManager.clear_all")

    @property
    def active_count(self) -> int:
        """Get the number of active toasts."""
        return len(self._active_toasts)

    @property
    def pending_count(self) -> int:
        """Get the number of pending toasts."""
        return len(self._pending_toasts)


def show_toast(
    message: str,
    level: ToastLevel = ToastLevel.INFO,
    title: str | None = None,
    duration_ms: int | None = None,
) -> None:
    """Convenience function to show a toast notification.

    Args:
        message: The message to display
        level: The notification level
        title: Optional title override
        duration_ms: Optional duration override
    """
    logger.debug(
        "Entering show_toast",
        extra={"level": level.value, "toast_msg": message},
    )

    # Build notification with provided or default values
    if duration_ms is not None:
        notification = ToastNotification(
            message=message,
            level=level,
            title=title,
            duration_ms=duration_ms,
        )
    else:
        notification = ToastNotification(
            message=message,
            level=level,
            title=title,
        )

    # Emit signal instead of using manager directly
    # This allows the manager to be lazily initialized
    signals = get_signals()
    signals.toast_requested.emit(notification)

    logger.debug("Exiting show_toast")


def show_success(message: str, title: str | None = None) -> None:
    """Show a success toast."""
    show_toast(message, ToastLevel.SUCCESS, title)


def show_error(message: str, title: str | None = None) -> None:
    """Show an error toast."""
    show_toast(message, ToastLevel.ERROR, title)


def show_warning(message: str, title: str | None = None) -> None:
    """Show a warning toast."""
    show_toast(message, ToastLevel.WARNING, title)


def show_info(message: str, title: str | None = None) -> None:
    """Show an info toast."""
    show_toast(message, ToastLevel.INFO, title)
