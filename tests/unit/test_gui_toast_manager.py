"""Tests for src.gui.toast_manager module.

Tests cover ToastConfig, ToastWidget, ToastManager, and convenience functions.
"""

import pytest

from src.gui.signals import ToastLevel, ToastNotification, get_signals, reset_signals
from src.gui.toast_manager import (
    ToastConfig,
    ToastManager,
    ToastWidget,
    show_error,
    show_info,
    show_success,
    show_toast,
    show_warning,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def signals():
    """Provide fresh signals instance."""
    reset_signals()
    yield get_signals()
    reset_signals()


@pytest.fixture
def toast_config():
    """Provide a ToastConfig instance."""
    return ToastConfig(
        default_duration_ms=1000,
        fade_duration_ms=100,
        max_visible=3,
        spacing=5,
        margin_right=10,
        margin_bottom=10,
    )


@pytest.fixture
def toast_notification():
    """Provide a ToastNotification instance."""
    return ToastNotification(
        message="Test message",
        level=ToastLevel.INFO,
        title="Test Title",
    )


@pytest.fixture
def toast_manager(qtbot, signals, toast_config):
    """Provide a ToastManager instance."""
    ToastManager.reset_instance()
    manager = ToastManager(config=toast_config)
    yield manager
    manager.clear_all()
    ToastManager.reset_instance()


# ============================================================================
# ToastConfig Tests
# ============================================================================


class TestToastConfig:
    """Tests for ToastConfig dataclass."""

    def test_config_default_values(self):
        """Test that ToastConfig has sensible defaults."""
        config = ToastConfig()
        assert config.default_duration_ms == 4000
        assert config.fade_duration_ms == 300
        assert config.max_visible == 5
        assert config.spacing == 10
        assert config.margin_right == 20
        assert config.margin_bottom == 20

    def test_config_custom_values(self, toast_config):
        """Test that ToastConfig accepts custom values."""
        assert toast_config.default_duration_ms == 1000
        assert toast_config.fade_duration_ms == 100
        assert toast_config.max_visible == 3

    def test_config_is_dataclass(self):
        """Test that ToastConfig is a proper dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(ToastConfig)

    def test_config_equality(self):
        """Test ToastConfig equality comparison."""
        config1 = ToastConfig(default_duration_ms=1000)
        config2 = ToastConfig(default_duration_ms=1000)
        config3 = ToastConfig(default_duration_ms=2000)

        assert config1 == config2
        assert config1 != config3


# ============================================================================
# ToastWidget Tests
# ============================================================================


class TestToastWidget:
    """Tests for ToastWidget class."""

    def test_widget_creation_info(self, qtbot, toast_notification):
        """Test creating an info toast widget."""
        widget = ToastWidget(toast_notification)
        qtbot.addWidget(widget)

        assert widget._notification == toast_notification
        assert widget._title_label is not None
        assert widget._message_label is not None

    def test_widget_creation_success(self, qtbot):
        """Test creating a success toast widget."""
        notification = ToastNotification(
            message="Success!",
            level=ToastLevel.SUCCESS,
        )
        widget = ToastWidget(notification)
        qtbot.addWidget(widget)

        assert widget.notification.level == ToastLevel.SUCCESS

    def test_widget_creation_error(self, qtbot):
        """Test creating an error toast widget."""
        notification = ToastNotification(
            message="Error occurred",
            level=ToastLevel.ERROR,
            title="Error",
        )
        widget = ToastWidget(notification)
        qtbot.addWidget(widget)

        assert widget.notification.level == ToastLevel.ERROR

    def test_widget_creation_warning(self, qtbot):
        """Test creating a warning toast widget."""
        notification = ToastNotification(
            message="Warning!",
            level=ToastLevel.WARNING,
        )
        widget = ToastWidget(notification)
        qtbot.addWidget(widget)

        assert widget.notification.level == ToastLevel.WARNING

    def test_widget_has_level_icons(self):
        """Test that ToastWidget has icon mappings for all levels."""
        assert ToastLevel.SUCCESS in ToastWidget.LEVEL_ICONS
        assert ToastLevel.ERROR in ToastWidget.LEVEL_ICONS
        assert ToastLevel.WARNING in ToastWidget.LEVEL_ICONS
        assert ToastLevel.INFO in ToastWidget.LEVEL_ICONS

    def test_widget_has_level_colors(self):
        """Test that ToastWidget has color mappings for all levels."""
        assert ToastLevel.SUCCESS in ToastWidget.LEVEL_COLORS
        assert ToastLevel.ERROR in ToastWidget.LEVEL_COLORS
        assert ToastLevel.WARNING in ToastWidget.LEVEL_COLORS
        assert ToastLevel.INFO in ToastWidget.LEVEL_COLORS

    def test_widget_notification_property(self, qtbot, toast_notification):
        """Test the notification property."""
        widget = ToastWidget(toast_notification)
        qtbot.addWidget(widget)

        assert widget.notification is toast_notification
        assert widget.notification.message == "Test message"

    def test_widget_word_wrap_enabled(self, qtbot, toast_notification):
        """Test that message label has word wrap enabled."""
        widget = ToastWidget(toast_notification)
        qtbot.addWidget(widget)

        assert widget._message_label.wordWrap() is True

    def test_widget_max_width_set(self, qtbot, toast_notification):
        """Test that widget has maximum width constraints."""
        widget = ToastWidget(toast_notification)
        qtbot.addWidget(widget)

        assert widget.maximumWidth() == 350
        assert widget.minimumWidth() == 200


# ============================================================================
# ToastManager Tests
# ============================================================================


class TestToastManager:
    """Tests for ToastManager class."""

    def test_manager_creation(self, toast_manager):
        """Test creating a ToastManager."""
        assert toast_manager is not None
        assert toast_manager.active_count == 0
        assert toast_manager.pending_count == 0

    def test_manager_with_custom_config(self, qtbot, toast_config):
        """Test creating manager with custom config."""
        manager = ToastManager(config=toast_config)
        assert manager._config == toast_config
        manager.clear_all()

    def test_manager_singleton_instance(self, qtbot, signals):
        """Test singleton pattern."""
        ToastManager.reset_instance()
        instance1 = ToastManager.instance()
        instance2 = ToastManager.instance()

        assert instance1 is instance2
        ToastManager.reset_instance()

    def test_manager_reset_instance(self, qtbot, signals):
        """Test resetting singleton instance."""
        ToastManager.reset_instance()
        instance1 = ToastManager.instance()
        ToastManager.reset_instance()
        instance2 = ToastManager.instance()

        assert instance1 is not instance2
        ToastManager.reset_instance()

    def test_show_toast_returns_widget(self, toast_manager, toast_notification):
        """Test that show_toast returns a ToastWidget."""
        widget = toast_manager.show_toast(toast_notification)
        assert isinstance(widget, ToastWidget)
        assert toast_manager.active_count == 1

    def test_show_multiple_toasts(self, toast_manager):
        """Test showing multiple toasts."""
        notifications = [
            ToastNotification(message=f"Toast {i}", level=ToastLevel.INFO)
            for i in range(3)
        ]

        for notification in notifications:
            toast_manager.show_toast(notification)

        assert toast_manager.active_count == 3

    def test_max_visible_toasts(self, toast_manager):
        """Test that max_visible limit is enforced."""
        # Config has max_visible=3
        notifications = [
            ToastNotification(message=f"Toast {i}", level=ToastLevel.INFO)
            for i in range(5)
        ]

        for notification in notifications:
            toast_manager.show_toast(notification)

        assert toast_manager.active_count == 3
        assert toast_manager.pending_count == 2

    def test_dismiss_all_toasts(self, toast_manager):
        """Test dismissing all toasts."""
        for i in range(3):
            notification = ToastNotification(
                message=f"Toast {i}", level=ToastLevel.INFO
            )
            toast_manager.show_toast(notification)

        assert toast_manager.active_count == 3
        toast_manager.dismiss_all()
        # Dismiss starts animations, so count may not be 0 immediately

    def test_clear_all_toasts(self, toast_manager):
        """Test clearing all toasts immediately."""
        for i in range(3):
            notification = ToastNotification(
                message=f"Toast {i}", level=ToastLevel.INFO
            )
            toast_manager.show_toast(notification)

        toast_manager.clear_all()
        assert toast_manager.active_count == 0
        assert toast_manager.pending_count == 0

    def test_signal_connection(self, toast_manager, signals):
        """Test that manager responds to toast_requested signal."""
        notification = ToastNotification(message="Signal test", level=ToastLevel.INFO)

        # Emit signal
        signals.toast_requested.emit(notification)

        assert toast_manager.active_count == 1

    def test_active_count_property(self, toast_manager, toast_notification):
        """Test active_count property."""
        assert toast_manager.active_count == 0
        toast_manager.show_toast(toast_notification)
        assert toast_manager.active_count == 1

    def test_pending_count_property(self, toast_manager):
        """Test pending_count property."""
        assert toast_manager.pending_count == 0

        # Fill to max and add more
        for i in range(5):
            notification = ToastNotification(
                message=f"Toast {i}", level=ToastLevel.INFO
            )
            toast_manager.show_toast(notification)

        assert toast_manager.pending_count == 2


# ============================================================================
# Convenience Function Tests
# ============================================================================


class TestConvenienceFunctions:
    """Tests for show_toast and related convenience functions."""

    def test_show_toast_emits_signal(self, signals):
        """Test that show_toast emits toast_requested signal."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_toast("Test message", ToastLevel.INFO)

        assert len(received) == 1
        assert received[0].message == "Test message"
        assert received[0].level == ToastLevel.INFO

    def test_show_toast_with_title(self, signals):
        """Test show_toast with custom title."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_toast("Message", ToastLevel.SUCCESS, title="Custom Title")

        assert received[0].title == "Custom Title"

    def test_show_toast_with_duration(self, signals):
        """Test show_toast with custom duration."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_toast("Message", duration_ms=5000)

        assert received[0].duration_ms == 5000

    def test_show_toast_default_level(self, signals):
        """Test show_toast defaults to INFO level."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_toast("Default level test")

        assert received[0].level == ToastLevel.INFO

    def test_show_success(self, signals):
        """Test show_success convenience function."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_success("Operation completed")

        assert received[0].level == ToastLevel.SUCCESS
        assert received[0].message == "Operation completed"

    def test_show_success_with_title(self, signals):
        """Test show_success with custom title."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_success("Done", title="Success!")

        assert received[0].title == "Success!"

    def test_show_error(self, signals):
        """Test show_error convenience function."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_error("Something went wrong")

        assert received[0].level == ToastLevel.ERROR
        assert received[0].message == "Something went wrong"

    def test_show_error_with_title(self, signals):
        """Test show_error with custom title."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_error("Failed", title="Error!")

        assert received[0].title == "Error!"

    def test_show_warning(self, signals):
        """Test show_warning convenience function."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_warning("Be careful")

        assert received[0].level == ToastLevel.WARNING
        assert received[0].message == "Be careful"

    def test_show_warning_with_title(self, signals):
        """Test show_warning with custom title."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_warning("Caution", title="Warning!")

        assert received[0].title == "Warning!"

    def test_show_info(self, signals):
        """Test show_info convenience function."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_info("FYI")

        assert received[0].level == ToastLevel.INFO
        assert received[0].message == "FYI"

    def test_show_info_with_title(self, signals):
        """Test show_info with custom title."""
        received = []
        signals.toast_requested.connect(lambda n: received.append(n))

        show_info("Note", title="Information")

        assert received[0].title == "Information"


# ============================================================================
# Integration Tests
# ============================================================================


class TestToastManagerIntegration:
    """Integration tests for toast system."""

    def test_full_toast_lifecycle(self, toast_manager, signals):
        """Test complete toast lifecycle: signal -> display -> dismiss."""
        notification = ToastNotification(
            message="Lifecycle test",
            level=ToastLevel.SUCCESS,
            title="Test",
        )

        # Show via signal
        signals.toast_requested.emit(notification)
        assert toast_manager.active_count == 1

        # Clear immediately
        toast_manager.clear_all()
        assert toast_manager.active_count == 0

    def test_toast_queuing_and_processing(self, toast_manager):
        """Test that queued toasts are processed after dismissal."""
        # Show max toasts
        for i in range(3):
            notification = ToastNotification(
                message=f"Toast {i}", level=ToastLevel.INFO
            )
            toast_manager.show_toast(notification)

        # Queue more
        for i in range(2):
            notification = ToastNotification(
                message=f"Queued {i}", level=ToastLevel.INFO
            )
            toast_manager.show_toast(notification)

        assert toast_manager.active_count == 3
        assert toast_manager.pending_count == 2

        # Clear all
        toast_manager.clear_all()
        assert toast_manager.active_count == 0
        assert toast_manager.pending_count == 0

    def test_different_level_toasts(self, toast_manager):
        """Test showing toasts of different levels."""
        levels = [
            ToastLevel.SUCCESS,
            ToastLevel.ERROR,
            ToastLevel.WARNING,
        ]

        # Only test up to max_visible (config has max_visible=3)
        for level in levels:
            notification = ToastNotification(
                message=f"Level {level.value}",
                level=level,
            )
            widget = toast_manager.show_toast(notification)
            assert widget.notification.level == level

        # Verify all are active
        assert toast_manager.active_count == 3

        # Clear up
        toast_manager.clear_all()


# ============================================================================
# Edge Cases
# ============================================================================


class TestToastEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_message(self, qtbot, signals):
        """Test toast with empty message."""
        notification = ToastNotification(message="", level=ToastLevel.INFO)
        widget = ToastWidget(notification)
        qtbot.addWidget(widget)

        assert widget.notification.message == ""

    def test_long_message(self, qtbot, signals):
        """Test toast with very long message."""
        long_message = "A" * 500
        notification = ToastNotification(message=long_message, level=ToastLevel.INFO)
        widget = ToastWidget(notification)
        qtbot.addWidget(widget)

        assert widget.notification.message == long_message
        # Word wrap should handle it
        assert widget._message_label.wordWrap() is True

    def test_special_characters_in_message(self, qtbot, signals):
        """Test toast with special characters."""
        special_message = "Test <html>&nbsp;'quotes' \"double\" ñ 你好"
        notification = ToastNotification(message=special_message, level=ToastLevel.INFO)
        widget = ToastWidget(notification)
        qtbot.addWidget(widget)

        assert widget.notification.message == special_message

    def test_clear_empty_manager(self, toast_manager):
        """Test clearing an already empty manager."""
        assert toast_manager.active_count == 0
        toast_manager.clear_all()  # Should not raise
        assert toast_manager.active_count == 0

    def test_dismiss_empty_manager(self, toast_manager):
        """Test dismissing from empty manager."""
        assert toast_manager.active_count == 0
        toast_manager.dismiss_all()  # Should not raise
