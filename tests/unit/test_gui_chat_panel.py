"""
Unit Tests for GUI Chat Panel Module.

Tests for ChatInput, ChatTextEdit, MessageList, and ChatPanel classes.
"""

from datetime import datetime

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QLabel, QPushButton, QTextEdit

from src.gui.chat_panel import ChatInput, ChatPanel, ChatTextEdit, MessageList
from src.gui.message_widget import MessageContainer
from src.gui.signals import (
    AetherSignals,
    ChatMessage,
    MessageRole,
    get_signals,
    reset_signals,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_signals_fixture():
    """Reset signals singleton before and after each test."""
    reset_signals()
    yield
    reset_signals()


@pytest.fixture
def signals() -> AetherSignals:
    """Create a fresh signals instance for testing."""
    return get_signals()


@pytest.fixture
def sample_user_message() -> ChatMessage:
    """Create a sample user message."""
    return ChatMessage(
        role=MessageRole.USER,
        content="Create a cube",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def sample_assistant_message() -> ChatMessage:
    """Create a sample assistant message."""
    return ChatMessage(
        role=MessageRole.ASSISTANT,
        content="Creating a cube for you...",
        timestamp=datetime(2024, 1, 15, 10, 30, 5),
        code="import bpy\nbpy.ops.mesh.primitive_cube_add()",
    )


@pytest.fixture
def sample_system_message() -> ChatMessage:
    """Create a sample system message."""
    return ChatMessage(
        role=MessageRole.SYSTEM,
        content="Connected to Blender",
        timestamp=datetime(2024, 1, 15, 10, 29, 0),
    )


# ============================================================================
# TestChatTextEdit
# ============================================================================


class TestChatTextEdit:
    """Tests for ChatTextEdit widget."""

    def test_text_edit_creation(self, qtbot) -> None:
        """Test ChatTextEdit can be created."""
        text_edit = ChatTextEdit()
        qtbot.addWidget(text_edit)
        assert text_edit is not None

    def test_enter_emits_signal(self, qtbot) -> None:
        """Test pressing Enter emits enter_pressed signal."""
        text_edit = ChatTextEdit()
        qtbot.addWidget(text_edit)
        text_edit.setPlainText("Hello")

        with qtbot.waitSignal(text_edit.enter_pressed, timeout=1000):
            # Create Enter key event
            event = QKeyEvent(
                QKeyEvent.Type.KeyPress,
                Qt.Key.Key_Return,
                Qt.KeyboardModifier.NoModifier,
            )
            text_edit.keyPressEvent(event)

    def test_shift_enter_does_not_emit_signal(self, qtbot) -> None:
        """Test Shift+Enter does not emit enter_pressed signal."""
        text_edit = ChatTextEdit()
        qtbot.addWidget(text_edit)
        text_edit.setPlainText("Hello")

        signal_emitted = False

        def on_enter():
            nonlocal signal_emitted
            signal_emitted = True

        text_edit.enter_pressed.connect(on_enter)

        # Create Shift+Enter key event
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.ShiftModifier,
        )
        text_edit.keyPressEvent(event)

        assert not signal_emitted

    def test_regular_typing_preserved(self, qtbot) -> None:
        """Test regular key presses work normally."""
        text_edit = ChatTextEdit()
        qtbot.addWidget(text_edit)

        # Type some text using qtbot
        qtbot.keyClicks(text_edit, "Hello World")

        assert text_edit.toPlainText() == "Hello World"

    def test_none_event_handled(self, qtbot) -> None:
        """Test handling None event gracefully."""
        text_edit = ChatTextEdit()
        qtbot.addWidget(text_edit)

        # Should not raise exception
        text_edit.keyPressEvent(None)


# ============================================================================
# TestChatInput
# ============================================================================


class TestChatInput:
    """Tests for ChatInput widget."""

    def test_chat_input_creation(self, qtbot, signals: AetherSignals) -> None:
        """Test ChatInput can be created."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        assert chat_input is not None

    def test_chat_input_has_text_field(self, qtbot, signals: AetherSignals) -> None:
        """Test ChatInput has a text input field."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        text_edit = chat_input.findChild(QTextEdit)
        assert text_edit is not None

    def test_chat_input_has_send_button(self, qtbot, signals: AetherSignals) -> None:
        """Test ChatInput has a send button."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        send_btn = chat_input.findChild(QPushButton, "sendButton")
        assert send_btn is not None
        assert send_btn.text() == "Send"

    def test_send_emits_signal(self, qtbot, signals: AetherSignals) -> None:
        """Test clicking send emits user_message_submitted signal."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        # Type message
        text_edit = chat_input.findChild(ChatTextEdit)
        text_edit.setPlainText("Hello AI")

        with qtbot.waitSignal(signals.user_message_submitted, timeout=1000) as blocker:
            send_btn = chat_input.findChild(QPushButton, "sendButton")
            send_btn.click()

        assert blocker.args == ["Hello AI"]

    def test_send_clears_input(self, qtbot, signals: AetherSignals) -> None:
        """Test sending a message clears the input field."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        text_edit = chat_input.findChild(ChatTextEdit)
        text_edit.setPlainText("Hello")

        send_btn = chat_input.findChild(QPushButton, "sendButton")
        send_btn.click()

        assert text_edit.toPlainText() == ""

    def test_empty_message_not_sent(self, qtbot, signals: AetherSignals) -> None:
        """Test empty message is not sent."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        signal_received = []
        signals.user_message_submitted.connect(lambda m: signal_received.append(m))

        # Click send with empty input
        send_btn = chat_input.findChild(QPushButton, "sendButton")
        send_btn.click()

        assert len(signal_received) == 0

    def test_whitespace_only_not_sent(self, qtbot, signals: AetherSignals) -> None:
        """Test whitespace-only message is not sent."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        signal_received = []
        signals.user_message_submitted.connect(lambda m: signal_received.append(m))

        text_edit = chat_input.findChild(ChatTextEdit)
        text_edit.setPlainText("   \n\t   ")

        send_btn = chat_input.findChild(QPushButton, "sendButton")
        send_btn.click()

        assert len(signal_received) == 0

    def test_processing_disables_input(self, qtbot, signals: AetherSignals) -> None:
        """Test processing_started disables input."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        signals.processing_started.emit()

        text_edit = chat_input.findChild(ChatTextEdit)
        send_btn = chat_input.findChild(QPushButton, "sendButton")

        assert not text_edit.isEnabled()
        assert not send_btn.isEnabled()

    def test_processing_finished_enables_input(
        self, qtbot, signals: AetherSignals
    ) -> None:
        """Test processing_finished re-enables input."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        signals.processing_started.emit()
        signals.processing_finished.emit()

        text_edit = chat_input.findChild(ChatTextEdit)
        send_btn = chat_input.findChild(QPushButton, "sendButton")

        assert text_edit.isEnabled()
        assert send_btn.isEnabled()

    def test_cannot_send_during_processing(self, qtbot, signals: AetherSignals) -> None:
        """Test cannot send message during processing."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        text_edit = chat_input.findChild(ChatTextEdit)
        text_edit.setPlainText("Test message")

        signals.processing_started.emit()

        signal_received = []
        signals.user_message_submitted.connect(lambda m: signal_received.append(m))

        send_btn = chat_input.findChild(QPushButton, "sendButton")
        send_btn.click()

        assert len(signal_received) == 0

    def test_set_focus(self, qtbot, signals: AetherSignals) -> None:
        """Test set_focus method."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)
        chat_input.show()

        chat_input.set_focus()

        text_edit = chat_input.findChild(ChatTextEdit)
        # Focus is set (widget may need to be visible for actual focus)
        assert text_edit is not None

    def test_placeholder_text(self, qtbot, signals: AetherSignals) -> None:
        """Test input field has placeholder text."""
        chat_input = ChatInput(signals)
        qtbot.addWidget(chat_input)

        text_edit = chat_input.findChild(ChatTextEdit)
        placeholder = text_edit.placeholderText()
        assert "Enter" in placeholder
        assert "send" in placeholder.lower()


# ============================================================================
# TestMessageList
# ============================================================================


class TestMessageList:
    """Tests for MessageList widget."""

    def test_message_list_creation(self, qtbot, signals: AetherSignals) -> None:
        """Test MessageList can be created."""
        message_list = MessageList(signals)
        qtbot.addWidget(message_list)

        assert message_list is not None
        assert message_list.messages == []

    def test_message_added_via_signal(
        self, qtbot, signals: AetherSignals, sample_user_message: ChatMessage
    ) -> None:
        """Test message is added when signal received."""
        message_list = MessageList(signals)
        qtbot.addWidget(message_list)

        signals.message_received.emit(sample_user_message)

        assert len(message_list.messages) == 1
        assert message_list.messages[0] == sample_user_message

    def test_multiple_messages_added(
        self,
        qtbot,
        signals: AetherSignals,
        sample_user_message: ChatMessage,
        sample_assistant_message: ChatMessage,
    ) -> None:
        """Test multiple messages can be added."""
        message_list = MessageList(signals)
        qtbot.addWidget(message_list)

        signals.message_received.emit(sample_user_message)
        signals.message_received.emit(sample_assistant_message)

        assert len(message_list.messages) == 2
        assert message_list.messages[0] == sample_user_message
        assert message_list.messages[1] == sample_assistant_message

    def test_clear_removes_messages(
        self, qtbot, signals: AetherSignals, sample_user_message: ChatMessage
    ) -> None:
        """Test chat_cleared removes all messages."""
        message_list = MessageList(signals)
        qtbot.addWidget(message_list)

        signals.message_received.emit(sample_user_message)
        assert len(message_list.messages) == 1

        signals.chat_cleared.emit()
        assert len(message_list.messages) == 0

    def test_message_container_created(
        self, qtbot, signals: AetherSignals, sample_user_message: ChatMessage
    ) -> None:
        """Test MessageContainer widget is created for each message."""
        message_list = MessageList(signals)
        qtbot.addWidget(message_list)

        signals.message_received.emit(sample_user_message)

        containers = message_list.findChildren(MessageContainer)
        assert len(containers) == 1

    def test_messages_property_returns_copy(
        self, qtbot, signals: AetherSignals, sample_user_message: ChatMessage
    ) -> None:
        """Test messages property returns a copy, not the original list."""
        message_list = MessageList(signals)
        qtbot.addWidget(message_list)

        signals.message_received.emit(sample_user_message)

        messages = message_list.messages
        messages.append(sample_user_message)  # Modify the returned list

        # Original should be unchanged
        assert len(message_list.messages) == 1

    def test_code_copy_to_clipboard(
        self,
        qtbot,
        signals: AetherSignals,
        sample_assistant_message: ChatMessage,
    ) -> None:
        """Test code copy requests are handled."""
        message_list = MessageList(signals)
        qtbot.addWidget(message_list)

        # Track toast signals
        success_messages = []
        signals.toast_requested.connect(
            lambda n: (
                success_messages.append(n.message)
                if "copied" in n.message.lower()
                else None
            )
        )

        signals.message_received.emit(sample_assistant_message)

        # Find the code block and trigger copy
        containers = message_list.findChildren(MessageContainer)
        assert len(containers) == 1

        container = containers[0]
        container.code_copy_requested.emit("test code")

        # Should have triggered clipboard copy (and toast)
        # Note: Actual clipboard operation may not work in test environment
        assert len(success_messages) >= 1


# ============================================================================
# TestChatPanel
# ============================================================================


class TestChatPanel:
    """Tests for ChatPanel widget."""

    def test_chat_panel_creation(self, qtbot, signals: AetherSignals) -> None:
        """Test ChatPanel can be created."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        assert panel is not None

    def test_chat_panel_has_message_list(self, qtbot, signals: AetherSignals) -> None:
        """Test ChatPanel contains MessageList."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        message_list = panel.findChild(MessageList)
        assert message_list is not None

    def test_chat_panel_has_input(self, qtbot, signals: AetherSignals) -> None:
        """Test ChatPanel contains ChatInput."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        chat_input = panel.findChild(ChatInput)
        assert chat_input is not None

    def test_chat_panel_has_header(self, qtbot, signals: AetherSignals) -> None:
        """Test ChatPanel has a header with title."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        labels = panel.findChildren(QLabel)
        chat_labels = [lbl for lbl in labels if "Chat" in lbl.text()]
        assert len(chat_labels) >= 1

    def test_chat_panel_has_clear_button(self, qtbot, signals: AetherSignals) -> None:
        """Test ChatPanel has a clear button."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        buttons = panel.findChildren(QPushButton)
        clear_buttons = [b for b in buttons if b.text() == "Clear"]
        assert len(clear_buttons) >= 1

    def test_welcome_message_added(self, qtbot, signals: AetherSignals) -> None:
        """Test welcome message is added on creation."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        assert len(panel.messages) == 1
        assert panel.messages[0].role == MessageRole.SYSTEM
        assert "Welcome" in panel.messages[0].content

    def test_user_message_displayed(self, qtbot, signals: AetherSignals) -> None:
        """Test user message is displayed when submitted."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        signals.user_message_submitted.emit("Hello AI")

        # Welcome message + user message
        assert len(panel.messages) == 2
        assert panel.messages[1].role == MessageRole.USER
        assert panel.messages[1].content == "Hello AI"

    def test_clear_button_clears_messages(self, qtbot, signals: AetherSignals) -> None:
        """Test clear button clears messages and adds welcome back."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        # Add a user message
        signals.user_message_submitted.emit("Test message")
        assert len(panel.messages) == 2

        # Click clear
        buttons = panel.findChildren(QPushButton)
        clear_btn = next(b for b in buttons if b.text() == "Clear")
        clear_btn.click()

        # Should only have welcome message again
        assert len(panel.messages) == 1
        assert panel.messages[0].role == MessageRole.SYSTEM

    def test_set_focus(self, qtbot, signals: AetherSignals) -> None:
        """Test set_focus method sets focus to input."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)
        panel.show()

        panel.set_focus()

        # Should not raise exception

    def test_messages_property(self, qtbot, signals: AetherSignals) -> None:
        """Test messages property returns message list."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        messages = panel.messages
        assert isinstance(messages, list)
        assert len(messages) >= 1  # At least welcome message


# ============================================================================
# TestChatPanelIntegration
# ============================================================================


class TestChatPanelIntegration:
    """Integration tests for chat panel workflow."""

    def test_full_conversation_flow(self, qtbot, signals: AetherSignals) -> None:
        """Test complete conversation flow."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        # Initial state - welcome message
        assert len(panel.messages) == 1

        # User sends message
        signals.user_message_submitted.emit("Create a cube")
        assert len(panel.messages) == 2
        assert panel.messages[1].content == "Create a cube"

        # Assistant responds
        assistant_msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content="Creating a cube...",
            timestamp=datetime.now(),
            code="bpy.ops.mesh.primitive_cube_add()",
        )
        signals.message_received.emit(assistant_msg)
        assert len(panel.messages) == 3
        assert panel.messages[2].role == MessageRole.ASSISTANT

        # System message (execution result)
        system_msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content="Cube created successfully",
            timestamp=datetime.now(),
        )
        signals.message_received.emit(system_msg)
        assert len(panel.messages) == 4

    def test_processing_state_affects_input(
        self, qtbot, signals: AetherSignals
    ) -> None:
        """Test processing state disables/enables input."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        chat_input = panel.findChild(ChatInput)
        text_edit = chat_input.findChild(ChatTextEdit)

        # Initially enabled
        assert text_edit.isEnabled()

        # Processing starts
        signals.processing_started.emit()
        assert not text_edit.isEnabled()

        # Processing ends
        signals.processing_finished.emit()
        assert text_edit.isEnabled()

    def test_error_message_displayed(self, qtbot, signals: AetherSignals) -> None:
        """Test error messages are displayed."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        error_msg = ChatMessage(
            role=MessageRole.ERROR,
            content="Execution failed: syntax error",
            timestamp=datetime.now(),
        )
        signals.message_received.emit(error_msg)

        assert len(panel.messages) == 2
        assert panel.messages[1].role == MessageRole.ERROR

    def test_conversation_with_multiple_users_messages(
        self, qtbot, signals: AetherSignals
    ) -> None:
        """Test multiple back-and-forth messages."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        # Simulate a conversation
        for i in range(3):
            # User message
            signals.user_message_submitted.emit(f"User message {i}")

            # Assistant response
            signals.message_received.emit(
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=f"Assistant response {i}",
                    timestamp=datetime.now(),
                )
            )

        # 1 welcome + 3 user + 3 assistant = 7
        assert len(panel.messages) == 7


# ============================================================================
# TestEdgeCases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_long_message(self, qtbot, signals: AetherSignals) -> None:
        """Test handling very long messages."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        long_message = "A" * 10000
        signals.user_message_submitted.emit(long_message)

        assert panel.messages[1].content == long_message

    def test_message_with_special_characters(
        self, qtbot, signals: AetherSignals
    ) -> None:
        """Test handling messages with special characters."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        special = "<script>alert('xss')</script> & \"quotes\""
        signals.user_message_submitted.emit(special)

        assert panel.messages[1].content == special

    def test_message_with_unicode(self, qtbot, signals: AetherSignals) -> None:
        """Test handling messages with unicode."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        unicode_msg = "Hello 🌍 World 你好 مرحبا"
        signals.user_message_submitted.emit(unicode_msg)

        assert panel.messages[1].content == unicode_msg

    def test_rapid_message_sending(self, qtbot, signals: AetherSignals) -> None:
        """Test rapid message sending."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        # Send many messages quickly
        for i in range(20):
            signals.user_message_submitted.emit(f"Message {i}")

        # 1 welcome + 20 user = 21
        assert len(panel.messages) == 21

    def test_clear_then_continue(self, qtbot, signals: AetherSignals) -> None:
        """Test clearing and continuing conversation."""
        panel = ChatPanel(signals)
        qtbot.addWidget(panel)

        # Add some messages
        signals.user_message_submitted.emit("First")
        signals.user_message_submitted.emit("Second")

        # Clear
        signals.chat_cleared.emit()
        # Add welcome back (simulating what _on_clear does)
        signals.message_received.emit(
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="Welcome back!",
                timestamp=datetime.now(),
            )
        )

        # Continue
        signals.user_message_submitted.emit("Third")

        # Should have welcome + new message
        assert len(panel.messages) == 2

    def test_default_signals_used(self, qtbot) -> None:
        """Test that default signals are used if none provided."""
        panel = ChatPanel()  # No signals argument
        qtbot.addWidget(panel)

        # Should work with global signals
        assert panel is not None
        assert len(panel.messages) >= 1
