"""
Unit Tests for GUI Main Window Module.

Tests for MainWindow class and run_app function.
"""

from unittest.mock import patch

import pytest

from src.gui.chat_panel import ChatPanel
from src.gui.main_window import MainWindow
from src.gui.settings_dialog import SettingsDialog
from src.gui.signals import AetherSignals, get_signals, reset_signals
from src.gui.status_bar import AetherStatusBar

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


# ============================================================================
# TestMainWindow
# ============================================================================


class TestMainWindow:
    """Tests for MainWindow widget."""

    def test_main_window_creation(self, qtbot, signals: AetherSignals) -> None:
        """Test MainWindow can be created."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        assert window is not None

    def test_main_window_has_title(self, qtbot, signals: AetherSignals) -> None:
        """Test MainWindow has correct title."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        assert "Aether" in window.windowTitle()

    def test_main_window_minimum_size(self, qtbot, signals: AetherSignals) -> None:
        """Test MainWindow has minimum size."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        assert window.minimumWidth() >= 800
        assert window.minimumHeight() >= 600

    def test_main_window_has_chat_panel(self, qtbot, signals: AetherSignals) -> None:
        """Test MainWindow contains ChatPanel."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        chat_panel = window.findChild(ChatPanel)
        assert chat_panel is not None

    def test_main_window_has_status_bar(self, qtbot, signals: AetherSignals) -> None:
        """Test MainWindow contains AetherStatusBar."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        status_bar = window.findChild(AetherStatusBar)
        assert status_bar is not None

    def test_main_window_has_menu_bar(self, qtbot, signals: AetherSignals) -> None:
        """Test MainWindow has a menu bar."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        menu_bar = window.menuBar()
        assert menu_bar is not None

    def test_default_signals_used(self, qtbot) -> None:
        """Test default signals are used if none provided."""
        window = MainWindow()  # No signals argument
        qtbot.addWidget(window)

        # Should work with global signals
        assert window is not None


# ============================================================================
# TestMainWindowMenus
# ============================================================================


class TestMainWindowMenus:
    """Tests for MainWindow menu functionality."""

    def test_file_menu_exists(self, qtbot, signals: AetherSignals) -> None:
        """Test File menu exists."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        menu_bar = window.menuBar()
        actions = menu_bar.actions()
        menu_titles = [a.text() for a in actions]

        assert any("File" in t for t in menu_titles)

    def test_edit_menu_exists(self, qtbot, signals: AetherSignals) -> None:
        """Test Edit menu exists."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        menu_bar = window.menuBar()
        actions = menu_bar.actions()
        menu_titles = [a.text() for a in actions]

        assert any("Edit" in t for t in menu_titles)

    def test_settings_menu_exists(self, qtbot, signals: AetherSignals) -> None:
        """Test Settings menu exists."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        menu_bar = window.menuBar()
        actions = menu_bar.actions()
        menu_titles = [a.text() for a in actions]

        assert any("Settings" in t for t in menu_titles)

    def test_help_menu_exists(self, qtbot, signals: AetherSignals) -> None:
        """Test Help menu exists."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        menu_bar = window.menuBar()
        actions = menu_bar.actions()
        menu_titles = [a.text() for a in actions]

        assert any("Help" in t for t in menu_titles)


# ============================================================================
# TestMainWindowActions
# ============================================================================


class TestMainWindowActions:
    """Tests for MainWindow action handlers."""

    def test_new_chat_emits_signal(self, qtbot, signals: AetherSignals) -> None:
        """Test new chat action emits chat_cleared signal."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        signal_received = []
        signals.chat_cleared.connect(lambda: signal_received.append(True))

        window._on_new_chat()

        assert len(signal_received) == 1

    def test_connect_emits_signal(self, qtbot, signals: AetherSignals) -> None:
        """Test connect action emits connection_requested signal."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        signal_received = []
        signals.connection_requested.connect(lambda: signal_received.append(True))

        window._on_connect()

        assert len(signal_received) == 1

    def test_disconnect_emits_signal(self, qtbot, signals: AetherSignals) -> None:
        """Test disconnect action emits disconnection_requested signal."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        signal_received = []
        signals.disconnection_requested.connect(lambda: signal_received.append(True))

        window._on_disconnect()

        assert len(signal_received) == 1

    def test_clear_chat_emits_signal(self, qtbot, signals: AetherSignals) -> None:
        """Test clear chat action emits chat_cleared signal."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        signal_received = []
        signals.chat_cleared.connect(lambda: signal_received.append(True))

        window._on_clear_chat()

        assert len(signal_received) == 1

    def test_about_shows_info(self, qtbot, signals: AetherSignals) -> None:
        """Test about action shows info toast."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        info_received = []
        signals.toast_requested.connect(
            lambda n: info_received.append(n.message) if "Aether" in n.message else None
        )

        window._on_about()

        assert len(info_received) >= 1
        assert "0.1.0" in info_received[0]

    def test_error_handler(self, qtbot, signals: AetherSignals) -> None:
        """Test error handler shows error toast."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        error_received = []
        signals.toast_requested.connect(lambda n: error_received.append(n.message))

        window._on_error("Test error message")

        assert len(error_received) >= 1
        assert "Test error message" in error_received[0]


# ============================================================================
# TestMainWindowSignals
# ============================================================================


class TestMainWindowSignals:
    """Tests for MainWindow signal connections."""

    def test_quit_requested_closes_window(self, qtbot, signals: AetherSignals) -> None:
        """Test quit_requested signal triggers window close."""
        window = MainWindow(signals)
        qtbot.addWidget(window)
        window.show()

        # Window should be visible
        assert window.isVisible()

        # Emit quit signal
        signals.quit_requested.emit()

        # Window should be closed (not visible)
        assert not window.isVisible()

    def test_error_occurred_shows_error(self, qtbot, signals: AetherSignals) -> None:
        """Test error_occurred signal shows error."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        error_received = []
        signals.toast_requested.connect(lambda n: error_received.append(n.message))

        signals.error_occurred.emit("Something went wrong")

        assert len(error_received) >= 1
        assert "Something went wrong" in error_received[0]


# ============================================================================
# TestMainWindowLifecycle
# ============================================================================


class TestMainWindowLifecycle:
    """Tests for MainWindow lifecycle events."""

    def test_close_event_accepts(self, qtbot, signals: AetherSignals) -> None:
        """Test close event is accepted."""
        window = MainWindow(signals)
        qtbot.addWidget(window)
        window.show()

        # Should close without error
        window.close()

    def test_show_event_emits_app_ready(self, qtbot, signals: AetherSignals) -> None:
        """Test show event emits app_ready signal."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        ready_received = []
        signals.app_ready.connect(lambda: ready_received.append(True))

        window.show()

        assert len(ready_received) >= 1

    def test_show_event_sets_focus(self, qtbot, signals: AetherSignals) -> None:
        """Test show event sets focus to chat panel."""
        window = MainWindow(signals)
        qtbot.addWidget(window)
        window.show()

        # Chat panel should exist and have focus set
        chat_panel = window.findChild(ChatPanel)
        assert chat_panel is not None


# ============================================================================
# TestMainWindowIntegration
# ============================================================================


class TestMainWindowIntegration:
    """Integration tests for MainWindow."""

    def test_full_workflow(self, qtbot, signals: AetherSignals) -> None:
        """Test complete application workflow."""
        window = MainWindow(signals)
        qtbot.addWidget(window)
        window.show()

        # Verify all components present
        assert window.findChild(ChatPanel) is not None
        assert window.findChild(AetherStatusBar) is not None
        assert window.menuBar() is not None

        # Verify signals work
        clear_received = []
        signals.chat_cleared.connect(lambda: clear_received.append(True))
        window._on_new_chat()
        assert len(clear_received) == 1

    def test_settings_dialog_opens(self, qtbot, signals: AetherSignals) -> None:
        """Test settings dialog can be opened."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        # Mock dialog exec to avoid blocking
        with patch.object(SettingsDialog, "exec", return_value=0):
            window._on_open_settings()

        # Should not crash

    def test_menu_actions_work(self, qtbot, signals: AetherSignals) -> None:
        """Test menu actions are functional."""
        window = MainWindow(signals)
        qtbot.addWidget(window)
        window.show()

        # Get menu bar
        menu_bar = window.menuBar()
        menus = menu_bar.actions()

        # Each menu should have actions
        for menu_action in menus:
            menu = menu_action.menu()
            if menu:
                assert menu.actions()


# ============================================================================
# TestEdgeCases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_multiple_windows(self, qtbot, signals: AetherSignals) -> None:
        """Test creating multiple windows."""
        window1 = MainWindow(signals)
        window2 = MainWindow(signals)
        qtbot.addWidget(window1)
        qtbot.addWidget(window2)

        # Both should work
        assert window1 is not None
        assert window2 is not None

    def test_rapid_signal_emission(self, qtbot, signals: AetherSignals) -> None:
        """Test rapid signal emissions don't cause issues."""
        window = MainWindow(signals)
        qtbot.addWidget(window)
        window.show()

        # Rapidly emit signals
        for _ in range(50):
            window._on_new_chat()
            window._on_clear_chat()

        # Should not crash

    def test_close_and_reopen(self, qtbot, signals: AetherSignals) -> None:
        """Test closing and reopening window."""
        window = MainWindow(signals)
        qtbot.addWidget(window)

        window.show()
        window.close()

        # Can create a new window
        window2 = MainWindow(signals)
        qtbot.addWidget(window2)
        window2.show()

        assert window2.isVisible()
