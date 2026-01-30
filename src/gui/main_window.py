"""
Aether Main Window Module.

Main application window with chat panel, status bar, and menu.
Entry point for the GUI application.
"""

import sys

from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from src.gui.chat_panel import ChatPanel
from src.gui.settings_dialog import SettingsDialog
from src.gui.signals import AetherSignals, get_signals
from src.gui.status_bar import AetherStatusBar
from src.gui.styles import COLORS, get_full_stylesheet
from src.telemetry.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    Aether main application window.

    Contains:
    - Menu bar with File, Edit, Settings, Help
    - Chat panel (main content)
    - Status bar
    """

    def __init__(
        self,
        signals: AetherSignals | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize main window.

        Args:
            signals: AetherSignals instance for communication
            parent: Parent widget
        """
        super().__init__(parent)
        self._signals = signals or get_signals()
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()
        logger.info("MainWindow initialized")

    def _setup_ui(self) -> None:
        """Set up the main window UI."""
        # Window properties
        self.setWindowTitle("Aether - Natural Language Blender Interface")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        # Apply stylesheet
        self.setStyleSheet(get_full_stylesheet())

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Chat panel (main content)
        self._chat_panel = ChatPanel(self._signals, self)
        layout.addWidget(self._chat_panel, stretch=1)

        # Status bar
        self._status_bar = AetherStatusBar(self._signals, self)
        layout.addWidget(self._status_bar)

        # Set dark background
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLORS.bg_dark}; }}")

    def _setup_menu(self) -> None:
        """Set up the menu bar."""
        menubar = self.menuBar()
        if menubar is None:
            logger.warning("Failed to get menu bar")
            return

        # Apply menu styling
        menubar.setStyleSheet(
            f"""
            QMenuBar {{
                background-color: {COLORS.bg_medium};
                color: {COLORS.text_primary};
                border-bottom: 1px solid {COLORS.border_dark};
                padding: 4px;
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
        """
        )

        # File menu
        file_menu = menubar.addMenu("&File")
        if file_menu:
            self._setup_file_menu(file_menu)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        if edit_menu:
            self._setup_edit_menu(edit_menu)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        if settings_menu:
            self._setup_settings_menu(settings_menu)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        if help_menu:
            self._setup_help_menu(help_menu)

    def _setup_file_menu(self, menu: object) -> None:
        """Set up File menu actions."""
        # New chat
        new_action = QAction("&New Chat", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setToolTip("Start a new chat session")
        new_action.triggered.connect(self._on_new_chat)
        menu.addAction(new_action)  # type: ignore[union-attr]

        menu.addSeparator()  # type: ignore[union-attr]

        # Connect to Blender
        connect_action = QAction("&Connect to Blender", self)
        connect_action.setShortcut(QKeySequence("Ctrl+B"))
        connect_action.setToolTip("Connect to running Blender instance")
        connect_action.triggered.connect(self._on_connect)
        menu.addAction(connect_action)  # type: ignore[union-attr]

        # Disconnect
        disconnect_action = QAction("&Disconnect", self)
        disconnect_action.setToolTip("Disconnect from Blender")
        disconnect_action.triggered.connect(self._on_disconnect)
        menu.addAction(disconnect_action)  # type: ignore[union-attr]

        menu.addSeparator()  # type: ignore[union-attr]

        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setToolTip("Exit the application")
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)  # type: ignore[union-attr]

    def _setup_edit_menu(self, menu: object) -> None:
        """Set up Edit menu actions."""
        # Clear chat
        clear_action = QAction("&Clear Chat", self)
        clear_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_action.setToolTip("Clear chat history")
        clear_action.triggered.connect(self._on_clear_chat)
        menu.addAction(clear_action)  # type: ignore[union-attr]

    def _setup_settings_menu(self, menu: object) -> None:
        """Set up Settings menu actions."""
        # AI Provider settings
        provider_action = QAction("&AI Provider...", self)
        provider_action.setShortcut(QKeySequence("Ctrl+,"))
        provider_action.setToolTip("Configure AI provider and model")
        provider_action.triggered.connect(self._on_open_settings)
        menu.addAction(provider_action)  # type: ignore[union-attr]

    def _setup_help_menu(self, menu: object) -> None:
        """Set up Help menu actions."""
        # About
        about_action = QAction("&About Aether", self)
        about_action.setToolTip("About Aether")
        about_action.triggered.connect(self._on_about)
        menu.addAction(about_action)  # type: ignore[union-attr]

    def _connect_signals(self) -> None:
        """Connect to application signals."""
        self._signals.quit_requested.connect(self.close)
        self._signals.error_occurred.connect(self._on_error)

    # ========================================================================
    # Action Handlers
    # ========================================================================

    def _on_new_chat(self) -> None:
        """Handle new chat action."""
        logger.debug("New chat requested")
        self._signals.chat_cleared.emit()
        self._chat_panel.set_focus()

    def _on_connect(self) -> None:
        """Handle connect to Blender action."""
        logger.debug("Connect to Blender requested")
        self._signals.connection_requested.emit()

    def _on_disconnect(self) -> None:
        """Handle disconnect action."""
        logger.debug("Disconnect from Blender requested")
        self._signals.disconnection_requested.emit()

    def _on_clear_chat(self) -> None:
        """Handle clear chat action."""
        logger.debug("Clear chat requested from menu")
        self._signals.chat_cleared.emit()

    def _on_open_settings(self) -> None:
        """Handle open settings action."""
        logger.debug("Settings dialog requested")
        dialog = SettingsDialog(self._signals, self)
        dialog.exec()

    def _on_about(self) -> None:
        """Handle about action."""
        logger.debug("About dialog requested")
        self._signals.show_info(
            "Aether v0.1.0\n\n"
            "Natural Language Interface for Blender\n"
            "Create 3D animations through conversation."
        )

    def _on_error(self, error: str) -> None:
        """Handle error signal."""
        logger.error("Error received in MainWindow", extra={"error": error})
        self._signals.show_error(error)

    # ========================================================================
    # Overrides
    # ========================================================================

    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Handle window close event."""
        logger.info("Application closing")
        if event:
            event.accept()

    def showEvent(self, event: object) -> None:
        """Handle window show event."""
        super().showEvent(event)  # type: ignore[arg-type]
        self._chat_panel.set_focus()
        self._signals.app_ready.emit()
        logger.info("Application window shown")


def run_app() -> int:
    """
    Run the Aether application.

    Returns:
        Exit code from the application
    """
    logger.info("Starting Aether application")

    app = QApplication(sys.argv)
    app.setApplicationName("Aether")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Aether")

    # Apply global stylesheet
    app.setStyleSheet(get_full_stylesheet())

    window = MainWindow()
    window.show()

    logger.info("Entering application event loop")
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())
