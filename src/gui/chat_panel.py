"""
Aether Chat Panel Module.

Chat interface with message history display and input area.
Connects to signals for sending/receiving messages.
"""

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication, QKeyEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.gui.message_widget import MessageContainer
from src.gui.signals import AetherSignals, ChatMessage, MessageRole, get_signals
from src.gui.styles import COLORS, DIMS, FONTS
from src.telemetry.logger import get_logger

logger = get_logger(__name__)


class ChatInput(QFrame):
    """
    Chat input area with text field and send button.

    Features:
    - Multi-line text input
    - Enter to send, Shift+Enter for newline
    - Send button with disabled state during processing
    """

    def __init__(
        self,
        signals: AetherSignals | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize chat input.

        Args:
            signals: AetherSignals instance for communication
            parent: Parent widget
        """
        super().__init__(parent)
        self._signals = signals or get_signals()
        self._processing = False
        self._setup_ui()
        self._connect_signals()
        logger.debug("ChatInput initialized")

    def _setup_ui(self) -> None:
        """Set up the input area UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            DIMS.spacing_md, DIMS.spacing_sm, DIMS.spacing_md, DIMS.spacing_sm
        )
        layout.setSpacing(DIMS.spacing_sm)

        # Text input
        self._input = ChatTextEdit(self)
        self._input.setObjectName("chatInput")
        self._input.setPlaceholderText(
            "Type your message here... (Enter to send, Shift+Enter for newline)"
        )
        self._input.setMinimumHeight(50)
        self._input.setMaximumHeight(150)
        self._input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._input.enter_pressed.connect(self._on_send)
        layout.addWidget(self._input)

        # Send button
        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("sendButton")
        self._send_btn.setFixedSize(80, 50)
        self._send_btn.clicked.connect(self._on_send)
        self._send_btn.setToolTip("Send message (Enter)")
        layout.addWidget(self._send_btn)

        # Style the frame
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {COLORS.bg_medium};
                border-top: 1px solid {COLORS.border_dark};
            }}
        """
        )

    def _connect_signals(self) -> None:
        """Connect to application signals."""
        self._signals.processing_started.connect(self._on_processing_started)
        self._signals.processing_finished.connect(self._on_processing_finished)

    def _on_send(self) -> None:
        """Handle send button/enter press."""
        text = self._input.toPlainText().strip()
        if not text or self._processing:
            return

        logger.debug("Sending user message", extra={"message_length": len(text)})
        self._signals.user_message_submitted.emit(text)
        self._input.clear()

    def _on_processing_started(self) -> None:
        """Handle processing started."""
        self._processing = True
        self._send_btn.setEnabled(False)
        self._input.setEnabled(False)
        logger.debug("Chat input disabled during processing")

    def _on_processing_finished(self) -> None:
        """Handle processing finished."""
        self._processing = False
        self._send_btn.setEnabled(True)
        self._input.setEnabled(True)
        self._input.setFocus()
        logger.debug("Chat input re-enabled after processing")

    def set_focus(self) -> None:
        """Set focus to the input field."""
        self._input.setFocus()


class ChatTextEdit(QTextEdit):
    """Custom text edit that emits signal on Enter press."""

    from PyQt6.QtCore import pyqtSignal

    enter_pressed = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        """Handle key press events."""
        if event is None:
            return

        key = event.key()
        modifiers = event.modifiers()

        # Enter without Shift sends the message
        if (
            key in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and modifiers != Qt.KeyboardModifier.ShiftModifier
        ):
            self.enter_pressed.emit()
            return

        super().keyPressEvent(event)


class MessageList(QScrollArea):
    """
    Scrollable message list display.

    Displays all chat messages with auto-scroll to bottom.
    """

    def __init__(
        self,
        signals: AetherSignals | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize message list.

        Args:
            signals: AetherSignals instance for communication
            parent: Parent widget
        """
        super().__init__(parent)
        self._signals = signals or get_signals()
        self._messages: list[ChatMessage] = []
        self._setup_ui()
        self._connect_signals()
        logger.debug("MessageList initialized")

    def _setup_ui(self) -> None:
        """Set up the message list UI."""
        self.setObjectName("messageContainer")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget
        self._container = QWidget()
        self._container.setObjectName("messageListContainer")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, DIMS.spacing_md, 0, DIMS.spacing_md)
        self._layout.setSpacing(DIMS.spacing_xs)
        self._layout.addStretch()

        self.setWidget(self._container)

        # Style
        self.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: {COLORS.bg_dark};
                border: none;
            }}
            QWidget#messageListContainer {{
                background-color: {COLORS.bg_dark};
            }}
        """
        )

    def _connect_signals(self) -> None:
        """Connect to application signals."""
        self._signals.message_received.connect(self._on_message_received)
        self._signals.chat_cleared.connect(self._on_chat_cleared)

    def _on_message_received(self, message: ChatMessage) -> None:
        """Handle new message received."""
        logger.debug(
            "Message received in MessageList",
            extra={"role": message.role.value, "content_length": len(message.content)},
        )
        self._add_message(message)

    def _add_message(self, message: ChatMessage) -> None:
        """Add a message to the list."""
        self._messages.append(message)

        # Remove the stretch at the end
        stretch_item = self._layout.takeAt(self._layout.count() - 1)
        if stretch_item:
            del stretch_item

        # Add message widget
        msg_container = MessageContainer(message, self._container)
        msg_container.code_copy_requested.connect(self._copy_to_clipboard)
        self._layout.addWidget(msg_container)

        # Add stretch back
        self._layout.addStretch()

        # Scroll to bottom after adding
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the message list."""
        scrollbar = self.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def _on_chat_cleared(self) -> None:
        """Handle chat cleared signal."""
        logger.debug("Clearing message list")
        self._messages.clear()

        # Remove all widgets except the stretch
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
            self._signals.show_success("Code copied to clipboard!")
            logger.debug("Text copied to clipboard", extra={"length": len(text)})

    @property
    def messages(self) -> list[ChatMessage]:
        """Return list of messages."""
        return self._messages.copy()


class ChatPanel(QFrame):
    """
    Complete chat panel with message list and input.

    Main chat interface component.
    """

    def __init__(
        self,
        signals: AetherSignals | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize chat panel.

        Args:
            signals: AetherSignals instance for communication
            parent: Parent widget
        """
        super().__init__(parent)
        self._signals = signals or get_signals()
        self._setup_ui()
        self._connect_signals()
        self._add_welcome_message()
        logger.info("ChatPanel initialized")

    def _setup_ui(self) -> None:
        """Set up the chat panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Message list
        self._message_list = MessageList(self._signals, self)
        layout.addWidget(self._message_list, stretch=1)

        # Input area
        self._input = ChatInput(self._signals, self)
        layout.addWidget(self._input)

        # Style
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {COLORS.bg_dark};
            }}
        """
        )

    def _create_header(self) -> QFrame:
        """Create the chat panel header."""
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet(
            f"""
            QFrame {{
                background-color: {COLORS.bg_medium};
                border-bottom: 1px solid {COLORS.border_dark};
            }}
        """
        )

        layout = QHBoxLayout(header)
        layout.setContentsMargins(DIMS.spacing_md, 0, DIMS.spacing_md, 0)

        title = QLabel("💬 Chat")
        title.setStyleSheet(f"font-size: {FONTS.size_large}px; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(32)
        clear_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS.text_secondary};
                border: 1px solid {COLORS.border_medium};
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.bg_lighter};
            }}
        """
        )
        clear_btn.clicked.connect(self._on_clear)
        clear_btn.setToolTip("Clear chat history")
        layout.addWidget(clear_btn)

        return header

    def _connect_signals(self) -> None:
        """Connect to application signals."""
        self._signals.user_message_submitted.connect(self._on_user_message)

    def _add_welcome_message(self) -> None:
        """Add welcome message on initialization."""
        welcome_msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content="Welcome to Aether! 🎨 Tell me what you'd like to create in Blender.",
            timestamp=datetime.now(),
        )
        self._signals.message_received.emit(welcome_msg)

    def _on_user_message(self, text: str) -> None:
        """Handle user message submitted."""
        # Add user message to display
        user_msg = ChatMessage(
            role=MessageRole.USER,
            content=text,
            timestamp=datetime.now(),
        )
        self._signals.message_received.emit(user_msg)

    def _on_clear(self) -> None:
        """Handle clear button click."""
        logger.debug("Clear chat requested")
        self._signals.chat_cleared.emit()
        self._add_welcome_message()

    def set_focus(self) -> None:
        """Set focus to the input field."""
        self._input.set_focus()

    @property
    def messages(self) -> list[ChatMessage]:
        """Return list of messages."""
        return self._message_list.messages
