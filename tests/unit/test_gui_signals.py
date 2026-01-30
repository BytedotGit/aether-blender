"""
Tests for GUI Signals Module.

Tests the signal infrastructure and data classes.
"""

from datetime import datetime

from src.gui.signals import (
    AetherSignals,
    ChatMessage,
    ConnectionState,
    ExecutionResult,
    MessageRole,
    ToastLevel,
    ToastNotification,
    get_signals,
)


class TestMessageRole:
    """Test MessageRole enum."""

    def test_user_role_value(self) -> None:
        """Test USER role has correct value."""
        assert MessageRole.USER.value == "user"

    def test_assistant_role_value(self) -> None:
        """Test ASSISTANT role has correct value."""
        assert MessageRole.ASSISTANT.value == "assistant"

    def test_system_role_value(self) -> None:
        """Test SYSTEM role has correct value."""
        assert MessageRole.SYSTEM.value == "system"

    def test_error_role_value(self) -> None:
        """Test ERROR role has correct value."""
        assert MessageRole.ERROR.value == "error"


class TestConnectionState:
    """Test ConnectionState enum."""

    def test_all_states_exist(self) -> None:
        """Test all expected states exist."""
        states = [s.value for s in ConnectionState]
        assert "disconnected" in states
        assert "connecting" in states
        assert "connected" in states
        assert "error" in states


class TestToastLevel:
    """Test ToastLevel enum."""

    def test_all_levels_exist(self) -> None:
        """Test all expected levels exist."""
        levels = [level.value for level in ToastLevel]
        assert "info" in levels
        assert "success" in levels
        assert "warning" in levels
        assert "error" in levels


class TestChatMessage:
    """Test ChatMessage dataclass."""

    def test_create_message_with_required_fields(self) -> None:
        """Test creating message with required fields."""
        msg = ChatMessage(
            role=MessageRole.USER,
            content="Hello",
            timestamp=datetime.now(),
        )
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.code is None
        assert msg.metadata is None

    def test_create_message_with_code(self) -> None:
        """Test creating message with code block."""
        msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content="Here's the code:",
            timestamp=datetime.now(),
            code="import bpy",
        )
        assert msg.code == "import bpy"

    def test_create_message_with_metadata(self) -> None:
        """Test creating message with metadata."""
        msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content="System message",
            timestamp=datetime.now(),
            metadata={"key": "value"},
        )
        assert msg.metadata == {"key": "value"}


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_create_success_result(self) -> None:
        """Test creating success result."""
        result = ExecutionResult(
            success=True,
            code="print('hello')",
            output="hello",
        )
        assert result.success is True
        assert result.code == "print('hello')"
        assert result.output == "hello"
        assert result.error is None

    def test_create_failure_result(self) -> None:
        """Test creating failure result."""
        result = ExecutionResult(
            success=False,
            code="print(",
            error="SyntaxError",
            attempts=3,
        )
        assert result.success is False
        assert result.error == "SyntaxError"
        assert result.attempts == 3


class TestToastNotification:
    """Test ToastNotification dataclass."""

    def test_create_info_toast(self) -> None:
        """Test creating info toast."""
        toast = ToastNotification(message="Info message")
        assert toast.message == "Info message"
        assert toast.level == ToastLevel.INFO
        assert toast.duration_ms == 3000

    def test_create_error_toast(self) -> None:
        """Test creating error toast."""
        toast = ToastNotification(
            message="Error occurred",
            level=ToastLevel.ERROR,
            duration_ms=5000,
        )
        assert toast.level == ToastLevel.ERROR
        assert toast.duration_ms == 5000


class TestAetherSignals:
    """Test AetherSignals class."""

    def test_signals_creation(self, qtbot: object) -> None:
        """Test signals can be created."""
        signals = AetherSignals()
        assert signals is not None

    def test_get_signals_returns_instance(self, qtbot: object) -> None:
        """Test get_signals returns a signals instance."""
        signals = get_signals()
        assert isinstance(signals, AetherSignals)

    def test_get_signals_returns_same_instance(self, qtbot: object) -> None:
        """Test get_signals returns the same instance."""
        signals1 = get_signals()
        signals2 = get_signals()
        assert signals1 is signals2

    def test_user_message_signal_exists(self, qtbot: object) -> None:
        """Test user_message_submitted signal exists."""
        signals = AetherSignals()
        assert hasattr(signals, "user_message_submitted")

    def test_message_received_signal_exists(self, qtbot: object) -> None:
        """Test message_received signal exists."""
        signals = AetherSignals()
        assert hasattr(signals, "message_received")

    def test_connection_state_signal_exists(self, qtbot: object) -> None:
        """Test connection_state_changed signal exists."""
        signals = AetherSignals()
        assert hasattr(signals, "connection_state_changed")

    def test_toast_requested_signal_exists(self, qtbot: object) -> None:
        """Test toast_requested signal exists."""
        signals = AetherSignals()
        assert hasattr(signals, "toast_requested")


class TestAetherSignalsMethods:
    """Test AetherSignals convenience methods."""

    def test_show_toast_method(self, qtbot: object) -> None:
        """Test show_toast convenience method."""
        signals = AetherSignals()
        received: list[ToastNotification] = []

        def on_toast(notification: ToastNotification) -> None:
            received.append(notification)

        signals.toast_requested.connect(on_toast)
        signals.show_toast("Test message", ToastLevel.INFO)

        assert len(received) == 1
        assert received[0].message == "Test message"
        assert received[0].level == ToastLevel.INFO

    def test_show_success_method(self, qtbot: object) -> None:
        """Test show_success convenience method."""
        signals = AetherSignals()
        received: list[ToastNotification] = []

        signals.toast_requested.connect(lambda n: received.append(n))
        signals.show_success("Success!")

        assert len(received) == 1
        assert received[0].level == ToastLevel.SUCCESS

    def test_show_error_method(self, qtbot: object) -> None:
        """Test show_error convenience method."""
        signals = AetherSignals()
        received: list[ToastNotification] = []

        signals.toast_requested.connect(lambda n: received.append(n))
        signals.show_error("Error!")

        assert len(received) == 1
        assert received[0].level == ToastLevel.ERROR

    def test_send_message_method(self, qtbot: object) -> None:
        """Test send_message convenience method."""
        signals = AetherSignals()
        received: list[ChatMessage] = []

        signals.message_received.connect(lambda m: received.append(m))
        signals.send_message(MessageRole.USER, "Hello")

        assert len(received) == 1
        assert received[0].role == MessageRole.USER
        assert received[0].content == "Hello"
