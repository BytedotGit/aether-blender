"""
Aether GUI Package.

PyQt6-based graphical user interface for Aether.
Provides chat interface, settings, and status display.
"""

from src.gui.chat_panel import ChatInput, ChatPanel, MessageList
from src.gui.main_window import MainWindow, run_app
from src.gui.message_widget import CodeBlock, MessageBubble, MessageContainer
from src.gui.settings_dialog import SettingsDialog
from src.gui.signals import (
    AetherSignals,
    ChatMessage,
    ConnectionState,
    ExecutionResult,
    MessageRole,
    ToastLevel,
    ToastNotification,
    get_signals,
    reset_signals,
)
from src.gui.status_bar import AetherStatusBar, StatusIndicator
from src.gui.styles import (
    COLORS,
    DIMS,
    FONTS,
    ColorPalette,
    Dimensions,
    FontConfig,
    apply_stylesheet,
    get_base_stylesheet,
    get_chat_stylesheet,
    get_full_stylesheet,
    get_status_color,
    get_toast_stylesheet,
)
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

__all__ = [
    # Main application
    "MainWindow",
    "run_app",
    # Chat components
    "ChatPanel",
    "ChatInput",
    "MessageList",
    # Message widgets
    "MessageBubble",
    "MessageContainer",
    "CodeBlock",
    # Settings
    "SettingsDialog",
    # Signals
    "AetherSignals",
    "get_signals",
    "reset_signals",
    "ChatMessage",
    "MessageRole",
    "ConnectionState",
    "ToastLevel",
    "ToastNotification",
    "ExecutionResult",
    # Status bar
    "AetherStatusBar",
    "StatusIndicator",
    # Toast notifications
    "ToastConfig",
    "ToastManager",
    "ToastWidget",
    "show_toast",
    "show_success",
    "show_error",
    "show_warning",
    "show_info",
    # Styles
    "ColorPalette",
    "FontConfig",
    "Dimensions",
    "COLORS",
    "FONTS",
    "DIMS",
    "get_full_stylesheet",
    "get_base_stylesheet",
    "get_chat_stylesheet",
    "get_toast_stylesheet",
    "apply_stylesheet",
    "get_status_color",
]
