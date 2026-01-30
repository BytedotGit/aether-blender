"""
Aether Message Widget Module.

Individual message bubble widgets for chat display.
Supports user, assistant, system, and error message types.
"""

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.gui.signals import ChatMessage, MessageRole
from src.gui.styles import COLORS, DIMS, FONTS
from src.telemetry.logger import get_logger

logger = get_logger(__name__)


class CodeBlock(QFrame):
    """
    Code block widget for displaying Python code.

    Features:
    - Monospace font
    - Syntax highlighting (future)
    - Copy button
    """

    copy_clicked = pyqtSignal(str)

    def __init__(self, code: str, parent: QWidget | None = None) -> None:
        """
        Initialize code block.

        Args:
            code: The Python code to display
            parent: Parent widget
        """
        super().__init__(parent)
        self._code = code
        self._setup_ui()
        logger.debug("CodeBlock created", extra={"code_length": len(code)})

    def _setup_ui(self) -> None:
        """Set up the code block UI."""
        self.setObjectName("codeBlock")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header with language label and copy button
        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 8, 4)

        lang_label = QLabel("Python")
        lang_label.setStyleSheet(
            f"color: {COLORS.text_muted}; font-size: {FONTS.size_small}px;"
        )
        header.addWidget(lang_label)

        header.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedHeight(24)
        copy_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS.text_secondary};
                border: 1px solid {COLORS.border_medium};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: {FONTS.size_small}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.bg_lighter};
            }}
        """
        )
        copy_btn.clicked.connect(self._on_copy)
        header.addWidget(copy_btn)

        layout.addLayout(header)

        # Code content
        code_label = QLabel(self._code)
        code_label.setWordWrap(True)
        code_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        code_label.setFont(
            QFont(FONTS.family_mono.split(",")[0].strip(), FONTS.size_small)
        )
        code_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {COLORS.code_bg};
                color: {COLORS.text_primary};
                padding: 8px;
                border-radius: 0 0 {DIMS.radius_md}px {DIMS.radius_md}px;
            }}
        """
        )
        layout.addWidget(code_label)

        # Style the frame
        self.setStyleSheet(
            f"""
            QFrame#codeBlock {{
                background-color: {COLORS.code_bg};
                border: 1px solid {COLORS.code_border};
                border-radius: {DIMS.radius_md}px;
            }}
        """
        )

    def _on_copy(self) -> None:
        """Handle copy button click."""
        logger.debug("Code copy requested")
        self.copy_clicked.emit(self._code)
        # Note: Actual clipboard copy will be handled by parent

    @property
    def code(self) -> str:
        """Return the code content."""
        return self._code


class MessageBubble(QFrame):
    """
    Message bubble widget for chat messages.

    Displays message content with role-appropriate styling.
    """

    code_copy_requested = pyqtSignal(str)

    def __init__(
        self,
        message: ChatMessage,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize message bubble.

        Args:
            message: The chat message to display
            parent: Parent widget
        """
        super().__init__(parent)
        self._message = message
        self._setup_ui()
        logger.debug(
            "MessageBubble created",
            extra={"role": message.role.value, "content_length": len(message.content)},
        )

    def _setup_ui(self) -> None:
        """Set up the message bubble UI."""
        role = self._message.role

        # Set object name for styling
        object_names = {
            MessageRole.USER: "userBubble",
            MessageRole.ASSISTANT: "assistantBubble",
            MessageRole.SYSTEM: "systemMessage",
            MessageRole.ERROR: "errorMessage",
        }
        self.setObjectName(object_names.get(role, "assistantBubble"))

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            DIMS.bubble_padding,
            DIMS.bubble_padding,
            DIMS.bubble_padding,
            DIMS.bubble_padding,
        )
        layout.setSpacing(DIMS.spacing_sm)

        # Content label
        content_label = QLabel(self._message.content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        content_label.setOpenExternalLinks(True)
        content_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        layout.addWidget(content_label)

        # Code block if present
        if self._message.code:
            code_block = CodeBlock(self._message.code, self)
            code_block.copy_clicked.connect(self.code_copy_requested.emit)
            layout.addWidget(code_block)

        # Timestamp
        timestamp_label = QLabel(self._format_timestamp(self._message.timestamp))
        timestamp_label.setStyleSheet(
            f"color: {COLORS.text_muted}; font-size: {FONTS.size_small}px;"
        )
        timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(timestamp_label)

        # Apply role-specific styling
        self._apply_role_style(role)

        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setMaximumWidth(DIMS.bubble_max_width)

    def _apply_role_style(self, role: MessageRole) -> None:
        """Apply styling based on message role."""
        styles = {
            MessageRole.USER: f"""
                QFrame#userBubble {{
                    background-color: {COLORS.user_bubble};
                    border-radius: {DIMS.radius_lg}px;
                }}
            """,
            MessageRole.ASSISTANT: f"""
                QFrame#assistantBubble {{
                    background-color: {COLORS.assistant_bubble};
                    border: 1px solid {COLORS.border_medium};
                    border-radius: {DIMS.radius_lg}px;
                }}
            """,
            MessageRole.SYSTEM: f"""
                QFrame#systemMessage {{
                    background-color: {COLORS.system_bubble};
                    border-radius: {DIMS.radius_md}px;
                }}
            """,
            MessageRole.ERROR: f"""
                QFrame#errorMessage {{
                    background-color: {COLORS.error_bubble};
                    border: 1px solid {COLORS.error};
                    border-radius: {DIMS.radius_md}px;
                }}
            """,
        }
        self.setStyleSheet(styles.get(role, styles[MessageRole.ASSISTANT]))

    @staticmethod
    def _format_timestamp(timestamp: datetime) -> str:
        """Format timestamp for display."""
        return timestamp.strftime("%H:%M")

    @property
    def message(self) -> ChatMessage:
        """Return the chat message."""
        return self._message


class MessageContainer(QWidget):
    """
    Container widget that positions a message bubble correctly.

    User messages align right, assistant messages align left.
    """

    code_copy_requested = pyqtSignal(str)

    def __init__(
        self,
        message: ChatMessage,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize message container.

        Args:
            message: The chat message to display
            parent: Parent widget
        """
        super().__init__(parent)
        self._message = message
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the container layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            DIMS.spacing_md, DIMS.spacing_xs, DIMS.spacing_md, DIMS.spacing_xs
        )
        layout.setSpacing(0)

        bubble = MessageBubble(self._message, self)
        bubble.code_copy_requested.connect(self.code_copy_requested.emit)

        if self._message.role == MessageRole.USER:
            # User messages align right
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            # Assistant/system messages align left
            layout.addWidget(bubble)
            layout.addStretch()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    @property
    def message(self) -> ChatMessage:
        """Return the chat message."""
        return self._message
