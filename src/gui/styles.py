"""
Aether GUI Styles Module.

QSS stylesheets and theming for consistent dark-mode appearance.
Colors, fonts, and reusable style constants.
"""

from dataclasses import dataclass

from src.telemetry.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Color Palette
# ============================================================================


@dataclass(frozen=True)
class ColorPalette:
    """Aether color palette for dark theme."""

    # Primary colors
    primary: str = "#4A9EFF"  # Aether blue
    primary_dark: str = "#3A7ECC"
    primary_light: str = "#6AB4FF"

    # Status colors
    success: str = "#4AFF6E"
    warning: str = "#FFB84A"
    error: str = "#FF4A4A"
    info: str = "#4A9EFF"

    # Background colors
    bg_dark: str = "#1E1E1E"
    bg_medium: str = "#252526"
    bg_light: str = "#2D2D2D"
    bg_lighter: str = "#3C3C3C"

    # Text colors
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#CCCCCC"
    text_muted: str = "#808080"
    text_disabled: str = "#555555"

    # Border colors
    border_dark: str = "#1E1E1E"
    border_medium: str = "#3C3C3C"
    border_light: str = "#555555"

    # Message bubble colors
    user_bubble: str = "#3A7ECC"
    assistant_bubble: str = "#2D2D2D"
    system_bubble: str = "#3C3C3C"
    error_bubble: str = "#4A2020"

    # Code block colors
    code_bg: str = "#1A1A1A"
    code_border: str = "#3C3C3C"


# Default palette instance
COLORS = ColorPalette()


# ============================================================================
# Font Configuration
# ============================================================================


@dataclass(frozen=True)
class FontConfig:
    """Font configuration for the application."""

    # Font families
    family_default: str = "Segoe UI, system-ui, sans-serif"
    family_mono: str = "Cascadia Code, Consolas, monospace"

    # Font sizes
    size_small: int = 11
    size_normal: int = 13
    size_large: int = 15
    size_title: int = 18
    size_heading: int = 22

    # Line heights
    line_height: float = 1.4
    line_height_code: float = 1.3


FONTS = FontConfig()


# ============================================================================
# Dimension Constants
# ============================================================================


@dataclass(frozen=True)
class Dimensions:
    """UI dimension constants."""

    # Spacing
    spacing_xs: int = 4
    spacing_sm: int = 8
    spacing_md: int = 12
    spacing_lg: int = 16
    spacing_xl: int = 24

    # Border radius
    radius_sm: int = 4
    radius_md: int = 8
    radius_lg: int = 12

    # Touch targets
    min_touch_target: int = 44

    # Input fields
    input_height: int = 40
    button_height: int = 36

    # Message bubbles
    bubble_max_width: int = 600
    bubble_padding: int = 12


DIMS = Dimensions()


# ============================================================================
# Stylesheet Components
# ============================================================================


def get_base_stylesheet() -> str:
    """Return base QSS for the application."""
    return f"""
        /* Global Application Styles */
        QWidget {{
            background-color: {COLORS.bg_dark};
            color: {COLORS.text_primary};
            font-family: {FONTS.family_default};
            font-size: {FONTS.size_normal}px;
        }}

        /* Main Window */
        QMainWindow {{
            background-color: {COLORS.bg_dark};
        }}

        /* Scroll Areas */
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}

        QScrollBar:vertical {{
            background-color: {COLORS.bg_medium};
            width: 12px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background-color: {COLORS.bg_lighter};
            min-height: 30px;
            border-radius: 6px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS.border_light};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QScrollBar:horizontal {{
            background-color: {COLORS.bg_medium};
            height: 12px;
            margin: 0;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {COLORS.bg_lighter};
            min-width: 30px;
            border-radius: 6px;
            margin: 2px;
        }}

        /* Labels */
        QLabel {{
            color: {COLORS.text_primary};
            background-color: transparent;
        }}

        /* Buttons */
        QPushButton {{
            background-color: {COLORS.primary};
            color: {COLORS.text_primary};
            border: none;
            border-radius: {DIMS.radius_md}px;
            padding: {DIMS.spacing_sm}px {DIMS.spacing_md}px;
            min-height: {DIMS.button_height}px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {COLORS.primary_light};
        }}

        QPushButton:pressed {{
            background-color: {COLORS.primary_dark};
        }}

        QPushButton:disabled {{
            background-color: {COLORS.bg_lighter};
            color: {COLORS.text_disabled};
        }}

        /* Secondary Button */
        QPushButton[class="secondary"] {{
            background-color: {COLORS.bg_lighter};
            border: 1px solid {COLORS.border_light};
        }}

        QPushButton[class="secondary"]:hover {{
            background-color: {COLORS.bg_light};
            border-color: {COLORS.primary};
        }}

        /* Text Inputs */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {COLORS.bg_light};
            color: {COLORS.text_primary};
            border: 1px solid {COLORS.border_medium};
            border-radius: {DIMS.radius_md}px;
            padding: {DIMS.spacing_sm}px;
            selection-background-color: {COLORS.primary};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {COLORS.primary};
        }}

        QLineEdit:disabled, QTextEdit:disabled {{
            background-color: {COLORS.bg_medium};
            color: {COLORS.text_disabled};
        }}

        /* Combo Boxes */
        QComboBox {{
            background-color: {COLORS.bg_light};
            color: {COLORS.text_primary};
            border: 1px solid {COLORS.border_medium};
            border-radius: {DIMS.radius_md}px;
            padding: {DIMS.spacing_sm}px;
            min-height: {DIMS.input_height}px;
        }}

        QComboBox:hover {{
            border-color: {COLORS.primary};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {COLORS.bg_light};
            border: 1px solid {COLORS.border_medium};
            selection-background-color: {COLORS.primary};
        }}

        /* Group Boxes */
        QGroupBox {{
            background-color: {COLORS.bg_medium};
            border: 1px solid {COLORS.border_medium};
            border-radius: {DIMS.radius_md}px;
            margin-top: 16px;
            padding-top: 16px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
            color: {COLORS.text_secondary};
        }}

        /* Splitters */
        QSplitter::handle {{
            background-color: {COLORS.border_medium};
        }}

        QSplitter::handle:horizontal {{
            width: 2px;
        }}

        QSplitter::handle:vertical {{
            height: 2px;
        }}

        /* Status Bar */
        QStatusBar {{
            background-color: {COLORS.bg_medium};
            color: {COLORS.text_secondary};
            border-top: 1px solid {COLORS.border_dark};
        }}

        /* Menu Bar */
        QMenuBar {{
            background-color: {COLORS.bg_medium};
            color: {COLORS.text_primary};
            border-bottom: 1px solid {COLORS.border_dark};
        }}

        QMenuBar::item:selected {{
            background-color: {COLORS.bg_lighter};
        }}

        QMenu {{
            background-color: {COLORS.bg_light};
            border: 1px solid {COLORS.border_medium};
        }}

        QMenu::item:selected {{
            background-color: {COLORS.primary};
        }}

        /* Tool Tips */
        QToolTip {{
            background-color: {COLORS.bg_light};
            color: {COLORS.text_primary};
            border: 1px solid {COLORS.border_medium};
            padding: 4px 8px;
            border-radius: {DIMS.radius_sm}px;
        }}

        /* Dialogs */
        QDialog {{
            background-color: {COLORS.bg_dark};
        }}

        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {COLORS.border_medium};
            border-radius: {DIMS.radius_md}px;
            background-color: {COLORS.bg_medium};
        }}

        QTabBar::tab {{
            background-color: {COLORS.bg_light};
            color: {COLORS.text_secondary};
            padding: 8px 16px;
            border-top-left-radius: {DIMS.radius_md}px;
            border-top-right-radius: {DIMS.radius_md}px;
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {COLORS.bg_medium};
            color: {COLORS.text_primary};
        }}

        QTabBar::tab:hover:!selected {{
            background-color: {COLORS.bg_lighter};
        }}
    """


def get_chat_stylesheet() -> str:
    """Return QSS specifically for chat components."""
    return f"""
        /* Message Container */
        #messageContainer {{
            background-color: {COLORS.bg_dark};
        }}

        /* User Message Bubble */
        #userBubble {{
            background-color: {COLORS.user_bubble};
            border-radius: {DIMS.radius_lg}px;
            padding: {DIMS.bubble_padding}px;
            margin: {DIMS.spacing_sm}px;
        }}

        /* Assistant Message Bubble */
        #assistantBubble {{
            background-color: {COLORS.assistant_bubble};
            border: 1px solid {COLORS.border_medium};
            border-radius: {DIMS.radius_lg}px;
            padding: {DIMS.bubble_padding}px;
            margin: {DIMS.spacing_sm}px;
        }}

        /* System Message */
        #systemMessage {{
            background-color: {COLORS.system_bubble};
            border-radius: {DIMS.radius_md}px;
            padding: {DIMS.spacing_sm}px;
            margin: {DIMS.spacing_sm}px;
            color: {COLORS.text_secondary};
            font-size: {FONTS.size_small}px;
        }}

        /* Error Message */
        #errorMessage {{
            background-color: {COLORS.error_bubble};
            border: 1px solid {COLORS.error};
            border-radius: {DIMS.radius_md}px;
            padding: {DIMS.spacing_sm}px;
            margin: {DIMS.spacing_sm}px;
        }}

        /* Code Block */
        #codeBlock {{
            background-color: {COLORS.code_bg};
            border: 1px solid {COLORS.code_border};
            border-radius: {DIMS.radius_md}px;
            padding: {DIMS.spacing_md}px;
            font-family: {FONTS.family_mono};
            font-size: {FONTS.size_small}px;
        }}

        /* Input Area */
        #chatInput {{
            background-color: {COLORS.bg_light};
            border: 1px solid {COLORS.border_medium};
            border-radius: {DIMS.radius_lg}px;
            padding: {DIMS.spacing_md}px;
            font-size: {FONTS.size_normal}px;
        }}

        #chatInput:focus {{
            border-color: {COLORS.primary};
        }}

        /* Send Button */
        #sendButton {{
            background-color: {COLORS.primary};
            border-radius: {DIMS.radius_lg}px;
            min-width: 80px;
        }}

        #sendButton:disabled {{
            background-color: {COLORS.bg_lighter};
        }}
    """


def get_toast_stylesheet() -> str:
    """Return QSS for toast notifications."""
    return f"""
        /* Toast Container */
        #toastContainer {{
            background-color: transparent;
        }}

        /* Toast Base */
        #toast {{
            border-radius: {DIMS.radius_md}px;
            padding: {DIMS.spacing_md}px {DIMS.spacing_lg}px;
            margin: {DIMS.spacing_sm}px;
        }}

        /* Toast Variants */
        #toastInfo {{
            background-color: {COLORS.bg_light};
            border-left: 4px solid {COLORS.info};
        }}

        #toastSuccess {{
            background-color: {COLORS.bg_light};
            border-left: 4px solid {COLORS.success};
        }}

        #toastWarning {{
            background-color: {COLORS.bg_light};
            border-left: 4px solid {COLORS.warning};
        }}

        #toastError {{
            background-color: {COLORS.bg_light};
            border-left: 4px solid {COLORS.error};
        }}
    """


def get_full_stylesheet() -> str:
    """Return the complete application stylesheet."""
    logger.debug("Generating full stylesheet")
    return (
        get_base_stylesheet()
        + "\n"
        + get_chat_stylesheet()
        + "\n"
        + get_toast_stylesheet()
    )


# ============================================================================
# Style Helper Functions
# ============================================================================


def apply_stylesheet(widget: object | None, stylesheet: str = "") -> None:
    """Apply a stylesheet to a widget."""
    if widget is None:
        logger.warning("Cannot apply stylesheet to None widget")
        return

    if hasattr(widget, "setStyleSheet"):
        if not stylesheet:
            stylesheet = get_full_stylesheet()
        widget.setStyleSheet(stylesheet)  # type: ignore[union-attr]
        logger.debug("Stylesheet applied to widget")
    else:
        logger.warning("Widget does not support setStyleSheet")


def get_status_color(status: str) -> str:
    """Get color for a status indicator."""
    status_colors = {
        "connected": COLORS.success,
        "disconnected": COLORS.error,
        "connecting": COLORS.warning,
        "error": COLORS.error,
        "success": COLORS.success,
        "warning": COLORS.warning,
        "info": COLORS.info,
    }
    return status_colors.get(status.lower(), COLORS.text_muted)
