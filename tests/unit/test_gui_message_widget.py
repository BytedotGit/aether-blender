"""
Unit Tests for GUI Message Widget Module.

Tests for MessageBubble, CodeBlock, and MessageContainer classes.
"""

from datetime import datetime

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton

from src.gui.message_widget import CodeBlock, MessageBubble, MessageContainer
from src.gui.signals import ChatMessage, MessageRole

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_user_message() -> ChatMessage:
    """Create a sample user message."""
    return ChatMessage(
        role=MessageRole.USER,
        content="Hello, create a cube for me",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def sample_assistant_message() -> ChatMessage:
    """Create a sample assistant message."""
    return ChatMessage(
        role=MessageRole.ASSISTANT,
        content="I'll create a cube for you.",
        timestamp=datetime(2024, 1, 15, 10, 30, 5),
        code="import bpy\nbpy.ops.mesh.primitive_cube_add()",
    )


@pytest.fixture
def sample_system_message() -> ChatMessage:
    """Create a sample system message."""
    return ChatMessage(
        role=MessageRole.SYSTEM,
        content="Blender connected successfully",
        timestamp=datetime(2024, 1, 15, 10, 29, 0),
    )


@pytest.fixture
def sample_error_message() -> ChatMessage:
    """Create a sample error message."""
    return ChatMessage(
        role=MessageRole.ERROR,
        content="Failed to execute code: syntax error",
        timestamp=datetime(2024, 1, 15, 10, 31, 0),
    )


@pytest.fixture
def sample_code() -> str:
    """Sample Python code for code block tests."""
    return """import bpy

# Create a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "MyCube"
"""


# ============================================================================
# TestCodeBlock
# ============================================================================


class TestCodeBlock:
    """Tests for CodeBlock widget."""

    def test_code_block_creation(self, qtbot, sample_code: str) -> None:
        """Test that CodeBlock can be created with code."""
        code_block = CodeBlock(sample_code)
        qtbot.addWidget(code_block)

        assert code_block.code == sample_code
        assert code_block.objectName() == "codeBlock"

    def test_code_block_empty_code(self, qtbot) -> None:
        """Test CodeBlock with empty code."""
        code_block = CodeBlock("")
        qtbot.addWidget(code_block)

        assert code_block.code == ""

    def test_code_block_has_copy_button(self, qtbot, sample_code: str) -> None:
        """Test that CodeBlock has a copy button."""
        code_block = CodeBlock(sample_code)
        qtbot.addWidget(code_block)

        copy_btn = code_block.findChild(QPushButton)
        assert copy_btn is not None
        assert copy_btn.text() == "Copy"

    def test_code_block_has_language_label(self, qtbot, sample_code: str) -> None:
        """Test that CodeBlock has a language label."""
        code_block = CodeBlock(sample_code)
        qtbot.addWidget(code_block)

        labels = code_block.findChildren(QLabel)
        lang_labels = [lbl for lbl in labels if lbl.text() == "Python"]
        assert len(lang_labels) == 1

    def test_code_block_copy_signal(self, qtbot, sample_code: str) -> None:
        """Test that clicking copy emits signal with code."""
        code_block = CodeBlock(sample_code)
        qtbot.addWidget(code_block)

        with qtbot.waitSignal(code_block.copy_clicked, timeout=1000) as blocker:
            copy_btn = code_block.findChild(QPushButton)
            copy_btn.click()

        assert blocker.args == [sample_code]

    def test_code_block_code_property(self, qtbot, sample_code: str) -> None:
        """Test code property returns correct value."""
        code_block = CodeBlock(sample_code)
        qtbot.addWidget(code_block)

        assert code_block.code == sample_code

    def test_code_block_with_multiline_code(self, qtbot) -> None:
        """Test CodeBlock handles multiline code."""
        multiline = "line1\nline2\nline3\nline4\nline5"
        code_block = CodeBlock(multiline)
        qtbot.addWidget(code_block)

        assert code_block.code == multiline

    def test_code_block_with_special_characters(self, qtbot) -> None:
        """Test CodeBlock handles special characters."""
        special = 'print("Hello <world> & "friends"")'
        code_block = CodeBlock(special)
        qtbot.addWidget(code_block)

        assert code_block.code == special


# ============================================================================
# TestMessageBubble
# ============================================================================


class TestMessageBubble:
    """Tests for MessageBubble widget."""

    def test_user_bubble_creation(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test creating a user message bubble."""
        bubble = MessageBubble(sample_user_message)
        qtbot.addWidget(bubble)

        assert bubble.message == sample_user_message
        assert bubble.objectName() == "userBubble"

    def test_assistant_bubble_creation(
        self, qtbot, sample_assistant_message: ChatMessage
    ) -> None:
        """Test creating an assistant message bubble."""
        bubble = MessageBubble(sample_assistant_message)
        qtbot.addWidget(bubble)

        assert bubble.message == sample_assistant_message
        assert bubble.objectName() == "assistantBubble"

    def test_system_message_creation(
        self, qtbot, sample_system_message: ChatMessage
    ) -> None:
        """Test creating a system message bubble."""
        bubble = MessageBubble(sample_system_message)
        qtbot.addWidget(bubble)

        assert bubble.message == sample_system_message
        assert bubble.objectName() == "systemMessage"

    def test_error_message_creation(
        self, qtbot, sample_error_message: ChatMessage
    ) -> None:
        """Test creating an error message bubble."""
        bubble = MessageBubble(sample_error_message)
        qtbot.addWidget(bubble)

        assert bubble.message == sample_error_message
        assert bubble.objectName() == "errorMessage"

    def test_bubble_displays_content(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test that bubble displays message content."""
        bubble = MessageBubble(sample_user_message)
        qtbot.addWidget(bubble)

        labels = bubble.findChildren(QLabel)
        content_labels = [
            lbl for lbl in labels if sample_user_message.content in lbl.text()
        ]
        assert len(content_labels) >= 1

    def test_bubble_displays_timestamp(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test that bubble displays timestamp."""
        bubble = MessageBubble(sample_user_message)
        qtbot.addWidget(bubble)

        labels = bubble.findChildren(QLabel)
        # Timestamp is formatted as HH:MM
        timestamp_labels = [lbl for lbl in labels if "10:30" in lbl.text()]
        assert len(timestamp_labels) >= 1

    def test_bubble_with_code_has_code_block(
        self, qtbot, sample_assistant_message: ChatMessage
    ) -> None:
        """Test that bubble with code has CodeBlock."""
        bubble = MessageBubble(sample_assistant_message)
        qtbot.addWidget(bubble)

        code_blocks = bubble.findChildren(CodeBlock)
        assert len(code_blocks) == 1
        assert code_blocks[0].code == sample_assistant_message.code

    def test_bubble_without_code_has_no_code_block(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test that bubble without code has no CodeBlock."""
        bubble = MessageBubble(sample_user_message)
        qtbot.addWidget(bubble)

        code_blocks = bubble.findChildren(CodeBlock)
        assert len(code_blocks) == 0

    def test_bubble_code_copy_signal(
        self, qtbot, sample_assistant_message: ChatMessage
    ) -> None:
        """Test that code copy signal propagates from CodeBlock."""
        bubble = MessageBubble(sample_assistant_message)
        qtbot.addWidget(bubble)

        with qtbot.waitSignal(bubble.code_copy_requested, timeout=1000) as blocker:
            code_block = bubble.findChild(CodeBlock)
            copy_btn = code_block.findChild(QPushButton)
            copy_btn.click()

        assert blocker.args == [sample_assistant_message.code]

    def test_bubble_message_property(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test message property returns correct value."""
        bubble = MessageBubble(sample_user_message)
        qtbot.addWidget(bubble)

        assert bubble.message == sample_user_message
        assert bubble.message.role == MessageRole.USER
        assert bubble.message.content == sample_user_message.content

    def test_timestamp_format(self, qtbot) -> None:
        """Test timestamp formatting."""
        message = ChatMessage(
            role=MessageRole.USER,
            content="Test",
            timestamp=datetime(2024, 12, 25, 23, 59, 0),
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        labels = bubble.findChildren(QLabel)
        timestamp_labels = [lbl for lbl in labels if "23:59" in lbl.text()]
        assert len(timestamp_labels) >= 1

    def test_bubble_content_selectable(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test that bubble content is selectable."""
        bubble = MessageBubble(sample_user_message)
        qtbot.addWidget(bubble)

        labels = bubble.findChildren(QLabel)
        content_labels = [
            lbl for lbl in labels if sample_user_message.content in lbl.text()
        ]

        for label in content_labels:
            flags = label.textInteractionFlags()
            assert flags & Qt.TextInteractionFlag.TextSelectableByMouse


# ============================================================================
# TestMessageContainer
# ============================================================================


class TestMessageContainer:
    """Tests for MessageContainer widget."""

    def test_user_message_container(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test creating a container for user message."""
        container = MessageContainer(sample_user_message)
        qtbot.addWidget(container)

        assert container.message == sample_user_message

    def test_assistant_message_container(
        self, qtbot, sample_assistant_message: ChatMessage
    ) -> None:
        """Test creating a container for assistant message."""
        container = MessageContainer(sample_assistant_message)
        qtbot.addWidget(container)

        assert container.message == sample_assistant_message

    def test_container_has_bubble(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test that container contains a MessageBubble."""
        container = MessageContainer(sample_user_message)
        qtbot.addWidget(container)

        bubbles = container.findChildren(MessageBubble)
        assert len(bubbles) == 1

    def test_container_code_copy_signal(
        self, qtbot, sample_assistant_message: ChatMessage
    ) -> None:
        """Test that code copy signal propagates through container."""
        container = MessageContainer(sample_assistant_message)
        qtbot.addWidget(container)

        with qtbot.waitSignal(container.code_copy_requested, timeout=1000) as blocker:
            bubble = container.findChild(MessageBubble)
            code_block = bubble.findChild(CodeBlock)
            copy_btn = code_block.findChild(QPushButton)
            copy_btn.click()

        assert blocker.args == [sample_assistant_message.code]

    def test_container_message_property(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test message property returns correct value."""
        container = MessageContainer(sample_user_message)
        qtbot.addWidget(container)

        assert container.message == sample_user_message

    def test_user_message_layout_alignment(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test user messages align to the right."""
        container = MessageContainer(sample_user_message)
        qtbot.addWidget(container)
        container.show()

        # For user messages, stretch should be added first (left side)
        layout = container.layout()
        # Item 0 is stretch, Item 1 is bubble
        assert layout.count() == 2
        # The stretch item at position 0 indicates right alignment
        stretch_item = layout.itemAt(0)
        bubble_item = layout.itemAt(1)
        # Stretch item has no widget
        assert stretch_item.widget() is None
        # Bubble item has the MessageBubble
        assert isinstance(bubble_item.widget(), MessageBubble)

    def test_assistant_message_layout_alignment(
        self, qtbot, sample_assistant_message: ChatMessage
    ) -> None:
        """Test assistant messages align to the left."""
        container = MessageContainer(sample_assistant_message)
        qtbot.addWidget(container)
        container.show()

        # For assistant messages, bubble should be added first (left side)
        layout = container.layout()
        # Item 0 is bubble, Item 1 is stretch
        assert layout.count() == 2
        # Bubble item is first
        bubble_item = layout.itemAt(0)
        stretch_item = layout.itemAt(1)
        assert isinstance(bubble_item.widget(), MessageBubble)
        # Stretch item has no widget
        assert stretch_item.widget() is None

    def test_system_message_layout_alignment(
        self, qtbot, sample_system_message: ChatMessage
    ) -> None:
        """Test system messages align to the left."""
        container = MessageContainer(sample_system_message)
        qtbot.addWidget(container)
        container.show()

        # System messages should align left like assistant messages
        layout = container.layout()
        bubble_item = layout.itemAt(0)
        assert isinstance(bubble_item.widget(), MessageBubble)

    def test_error_message_layout_alignment(
        self, qtbot, sample_error_message: ChatMessage
    ) -> None:
        """Test error messages align to the left."""
        container = MessageContainer(sample_error_message)
        qtbot.addWidget(container)
        container.show()

        # Error messages should align left like assistant messages
        layout = container.layout()
        bubble_item = layout.itemAt(0)
        assert isinstance(bubble_item.widget(), MessageBubble)


# ============================================================================
# TestMessageRoleStyling
# ============================================================================


class TestMessageRoleStyling:
    """Tests for message role-specific styling."""

    def test_user_bubble_object_name(
        self, qtbot, sample_user_message: ChatMessage
    ) -> None:
        """Test user bubble has correct object name."""
        bubble = MessageBubble(sample_user_message)
        qtbot.addWidget(bubble)
        assert bubble.objectName() == "userBubble"

    def test_assistant_bubble_object_name(
        self, qtbot, sample_assistant_message: ChatMessage
    ) -> None:
        """Test assistant bubble has correct object name."""
        bubble = MessageBubble(sample_assistant_message)
        qtbot.addWidget(bubble)
        assert bubble.objectName() == "assistantBubble"

    def test_system_bubble_object_name(
        self, qtbot, sample_system_message: ChatMessage
    ) -> None:
        """Test system bubble has correct object name."""
        bubble = MessageBubble(sample_system_message)
        qtbot.addWidget(bubble)
        assert bubble.objectName() == "systemMessage"

    def test_error_bubble_object_name(
        self, qtbot, sample_error_message: ChatMessage
    ) -> None:
        """Test error bubble has correct object name."""
        bubble = MessageBubble(sample_error_message)
        qtbot.addWidget(bubble)
        assert bubble.objectName() == "errorMessage"

    def test_all_roles_have_stylesheet(
        self,
        qtbot,
        sample_user_message: ChatMessage,
        sample_assistant_message: ChatMessage,
        sample_system_message: ChatMessage,
        sample_error_message: ChatMessage,
    ) -> None:
        """Test all message roles have stylesheets applied."""
        for message in [
            sample_user_message,
            sample_assistant_message,
            sample_system_message,
            sample_error_message,
        ]:
            bubble = MessageBubble(message)
            qtbot.addWidget(bubble)
            assert bubble.styleSheet() != ""


# ============================================================================
# TestEdgeCases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_message_content(self, qtbot) -> None:
        """Test handling of empty message content."""
        message = ChatMessage(
            role=MessageRole.USER,
            content="",
            timestamp=datetime.now(),
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        assert bubble.message.content == ""

    def test_long_message_content(self, qtbot) -> None:
        """Test handling of very long message content."""
        long_content = "A" * 10000
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=long_content,
            timestamp=datetime.now(),
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        assert bubble.message.content == long_content

    def test_message_with_newlines(self, qtbot) -> None:
        """Test handling of message with newlines."""
        content = "Line 1\nLine 2\nLine 3"
        message = ChatMessage(
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now(),
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        assert bubble.message.content == content

    def test_message_with_html_characters(self, qtbot) -> None:
        """Test handling of message with HTML-like characters."""
        content = "<script>alert('xss')</script>"
        message = ChatMessage(
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now(),
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        # Content should be preserved (Qt handles escaping)
        assert bubble.message.content == content

    def test_message_with_unicode(self, qtbot) -> None:
        """Test handling of message with unicode characters."""
        content = "Hello 🌍 World 你好 مرحبا"
        message = ChatMessage(
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now(),
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        assert bubble.message.content == content

    def test_code_block_with_empty_code(self, qtbot) -> None:
        """Test CodeBlock with empty code string."""
        code_block = CodeBlock("")
        qtbot.addWidget(code_block)

        assert code_block.code == ""

    def test_message_with_only_code(self, qtbot) -> None:
        """Test message with code but minimal content."""
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=".",
            timestamp=datetime.now(),
            code="print('hello')",
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        code_blocks = bubble.findChildren(CodeBlock)
        assert len(code_blocks) == 1

    def test_message_with_metadata(self, qtbot) -> None:
        """Test message with metadata is handled correctly."""
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content="Response with metadata",
            timestamp=datetime.now(),
            metadata={"tokens": 100, "model": "gemini-1.5-flash"},
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        assert bubble.message.metadata == {"tokens": 100, "model": "gemini-1.5-flash"}

    def test_midnight_timestamp(self, qtbot) -> None:
        """Test handling of midnight timestamp."""
        message = ChatMessage(
            role=MessageRole.USER,
            content="Midnight message",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        labels = bubble.findChildren(QLabel)
        timestamp_labels = [lbl for lbl in labels if "00:00" in lbl.text()]
        assert len(timestamp_labels) >= 1


# ============================================================================
# TestIntegration
# ============================================================================


class TestIntegration:
    """Integration tests for message widget components."""

    def test_full_message_flow(self, qtbot) -> None:
        """Test complete message display flow."""
        # Create a message with all features
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content="Here's your cube:",
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
            code="import bpy\nbpy.ops.mesh.primitive_cube_add()",
        )

        # Create container
        container = MessageContainer(message)
        qtbot.addWidget(container)
        container.show()

        # Verify structure
        bubbles = container.findChildren(MessageBubble)
        assert len(bubbles) == 1

        code_blocks = container.findChildren(CodeBlock)
        assert len(code_blocks) == 1

        # Verify signal chain works
        signal_received = []

        def capture_signal(code: str) -> None:
            signal_received.append(code)

        container.code_copy_requested.connect(capture_signal)

        # Trigger copy
        code_block = code_blocks[0]
        copy_btn = code_block.findChild(QPushButton)
        copy_btn.click()

        assert len(signal_received) == 1
        assert signal_received[0] == message.code

    def test_multiple_messages(self, qtbot) -> None:
        """Test creating multiple message containers."""
        messages = [
            ChatMessage(
                role=MessageRole.USER,
                content="Create a cube",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
            ),
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content="Creating cube...",
                timestamp=datetime(2024, 1, 15, 10, 0, 5),
                code="bpy.ops.mesh.primitive_cube_add()",
            ),
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="Execution complete",
                timestamp=datetime(2024, 1, 15, 10, 0, 6),
            ),
        ]

        containers = []
        for msg in messages:
            container = MessageContainer(msg)
            qtbot.addWidget(container)
            containers.append(container)

        assert len(containers) == 3
        assert containers[0].message.role == MessageRole.USER
        assert containers[1].message.role == MessageRole.ASSISTANT
        assert containers[2].message.role == MessageRole.SYSTEM

    def test_conversation_with_errors(self, qtbot) -> None:
        """Test conversation that includes error messages."""
        messages = [
            ChatMessage(
                role=MessageRole.USER,
                content="Run invalid code",
                timestamp=datetime.now(),
            ),
            ChatMessage(
                role=MessageRole.ERROR,
                content="SyntaxError: invalid syntax",
                timestamp=datetime.now(),
            ),
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content="Let me fix that...",
                timestamp=datetime.now(),
            ),
        ]

        containers = []
        for msg in messages:
            container = MessageContainer(msg)
            qtbot.addWidget(container)
            containers.append(container)

        # Error message should have error styling
        error_container = containers[1]
        error_bubble = error_container.findChild(MessageBubble)
        assert error_bubble.objectName() == "errorMessage"
