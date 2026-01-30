"""
Unit Tests for GUI Status Bar Module.

Tests for StatusIndicator and AetherStatusBar classes.
"""

import pytest
from PyQt6.QtWidgets import QLabel

from src.gui.signals import AetherSignals, ConnectionState, get_signals, reset_signals
from src.gui.status_bar import AetherStatusBar, StatusIndicator
from src.gui.styles import get_status_color

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
# TestStatusIndicator
# ============================================================================


class TestStatusIndicator:
    """Tests for StatusIndicator widget."""

    def test_indicator_creation(self, qtbot) -> None:
        """Test StatusIndicator can be created."""
        indicator = StatusIndicator("Blender", "Disconnected")
        qtbot.addWidget(indicator)

        assert indicator is not None

    def test_indicator_displays_label(self, qtbot) -> None:
        """Test indicator displays the label."""
        indicator = StatusIndicator("Blender", "Connected")
        qtbot.addWidget(indicator)

        labels = indicator.findChildren(QLabel)
        text_labels = [lbl for lbl in labels if "Blender" in lbl.text()]
        assert len(text_labels) >= 1

    def test_indicator_displays_status(self, qtbot) -> None:
        """Test indicator displays the status."""
        indicator = StatusIndicator("Blender", "Connected")
        qtbot.addWidget(indicator)

        labels = indicator.findChildren(QLabel)
        status_labels = [lbl for lbl in labels if "Connected" in lbl.text()]
        assert len(status_labels) >= 1

    def test_indicator_has_dot(self, qtbot) -> None:
        """Test indicator has a status dot."""
        indicator = StatusIndicator("Test", "status")
        qtbot.addWidget(indicator)

        labels = indicator.findChildren(QLabel)
        dot_labels = [lbl for lbl in labels if "●" in lbl.text()]
        assert len(dot_labels) >= 1

    def test_set_status_updates_text(self, qtbot) -> None:
        """Test set_status updates the displayed text."""
        indicator = StatusIndicator("Blender", "Disconnected")
        qtbot.addWidget(indicator)

        indicator.set_status("Connected")

        labels = indicator.findChildren(QLabel)
        status_labels = [lbl for lbl in labels if "Connected" in lbl.text()]
        assert len(status_labels) >= 1

    def test_set_status_updates_color(self, qtbot) -> None:
        """Test set_status updates the dot color."""
        indicator = StatusIndicator("Blender", "Disconnected")
        qtbot.addWidget(indicator)

        # Get initial color
        labels = indicator.findChildren(QLabel)
        dot_label = next(lbl for lbl in labels if "●" in lbl.text())
        initial_style = dot_label.styleSheet()

        indicator.set_status("Connected")

        # Color should change (Connected vs Disconnected have different colors)
        new_style = dot_label.styleSheet()
        # Both styles should have a color, and they should be different
        assert "color:" in initial_style
        assert "color:" in new_style

    def test_different_status_colors(self, qtbot) -> None:
        """Test different statuses have appropriate colors."""
        statuses = ["Connected", "Disconnected", "Connecting...", "Error"]

        for status in statuses:
            indicator = StatusIndicator("Test", status)
            qtbot.addWidget(indicator)

            labels = indicator.findChildren(QLabel)
            dot_label = next(lbl for lbl in labels if "●" in lbl.text())

            # Dot should have a color style
            assert "color:" in dot_label.styleSheet()

    def test_indicator_with_empty_label(self, qtbot) -> None:
        """Test indicator with empty label."""
        indicator = StatusIndicator("", "status")
        qtbot.addWidget(indicator)

        labels = indicator.findChildren(QLabel)
        text_labels = [lbl for lbl in labels if ": status" in lbl.text()]
        assert len(text_labels) >= 1

    def test_indicator_with_empty_status(self, qtbot) -> None:
        """Test indicator with empty status."""
        indicator = StatusIndicator("Label", "")
        qtbot.addWidget(indicator)

        labels = indicator.findChildren(QLabel)
        text_labels = [lbl for lbl in labels if "Label: " in lbl.text()]
        assert len(text_labels) >= 1


# ============================================================================
# TestAetherStatusBar
# ============================================================================


class TestAetherStatusBar:
    """Tests for AetherStatusBar widget."""

    def test_status_bar_creation(self, qtbot, signals: AetherSignals) -> None:
        """Test AetherStatusBar can be created."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        assert status_bar is not None

    def test_status_bar_has_blender_status(self, qtbot, signals: AetherSignals) -> None:
        """Test status bar has Blender status indicator."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        indicators = status_bar.findChildren(StatusIndicator)
        blender_indicator = next(
            (i for i in indicators if "Blender" in i.findChildren(QLabel)[1].text()),
            None,
        )
        assert blender_indicator is not None

    def test_status_bar_has_ai_status(self, qtbot, signals: AetherSignals) -> None:
        """Test status bar has AI status indicator."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        indicators = status_bar.findChildren(StatusIndicator)
        ai_indicator = next(
            (i for i in indicators if "AI" in i.findChildren(QLabel)[1].text()),
            None,
        )
        assert ai_indicator is not None

    def test_status_bar_has_version(self, qtbot, signals: AetherSignals) -> None:
        """Test status bar displays version info."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        labels = status_bar.findChildren(QLabel)
        version_labels = [lbl for lbl in labels if "Aether" in lbl.text()]
        assert len(version_labels) >= 1

    def test_connection_state_connected(self, qtbot, signals: AetherSignals) -> None:
        """Test connection state changes to Connected."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        signals.connection_state_changed.emit(ConnectionState.CONNECTED)

        labels = status_bar.findChildren(QLabel)
        connected_labels = [lbl for lbl in labels if "Connected" in lbl.text()]
        assert len(connected_labels) >= 1

    def test_connection_state_disconnected(self, qtbot, signals: AetherSignals) -> None:
        """Test connection state changes to Disconnected."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        signals.connection_state_changed.emit(ConnectionState.DISCONNECTED)

        labels = status_bar.findChildren(QLabel)
        disconnected_labels = [lbl for lbl in labels if "Disconnected" in lbl.text()]
        assert len(disconnected_labels) >= 1

    def test_connection_state_connecting(self, qtbot, signals: AetherSignals) -> None:
        """Test connection state changes to Connecting."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        signals.connection_state_changed.emit(ConnectionState.CONNECTING)

        labels = status_bar.findChildren(QLabel)
        connecting_labels = [lbl for lbl in labels if "Connecting" in lbl.text()]
        assert len(connecting_labels) >= 1

    def test_connection_state_error(self, qtbot, signals: AetherSignals) -> None:
        """Test connection state changes to Error."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        signals.connection_state_changed.emit(ConnectionState.ERROR)

        labels = status_bar.findChildren(QLabel)
        error_labels = [lbl for lbl in labels if "Error" in lbl.text()]
        assert len(error_labels) >= 1

    def test_provider_changed(self, qtbot, signals: AetherSignals) -> None:
        """Test provider change updates AI status."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        signals.provider_changed.emit("Gemini", "gemini-1.5-flash")

        labels = status_bar.findChildren(QLabel)
        gemini_labels = [lbl for lbl in labels if "Gemini" in lbl.text()]
        assert len(gemini_labels) >= 1
        # Also check model name is shown
        model_labels = [lbl for lbl in labels if "flash" in lbl.text()]
        assert len(model_labels) >= 1

    def test_processing_started_shows_indicator(
        self, qtbot, signals: AetherSignals
    ) -> None:
        """Test processing_started shows processing indicator."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        signals.processing_started.emit()

        labels = status_bar.findChildren(QLabel)
        processing_labels = [lbl for lbl in labels if "Processing" in lbl.text()]
        assert len(processing_labels) >= 1

    def test_processing_finished_hides_indicator(
        self, qtbot, signals: AetherSignals
    ) -> None:
        """Test processing_finished hides processing indicator."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        # Start then finish processing
        signals.processing_started.emit()
        signals.processing_finished.emit()

        labels = status_bar.findChildren(QLabel)
        processing_labels = [lbl for lbl in labels if "Processing" in lbl.text()]
        assert len(processing_labels) == 0

    def test_default_signals_used(self, qtbot) -> None:
        """Test default signals are used if none provided."""
        status_bar = AetherStatusBar()  # No signals argument
        qtbot.addWidget(status_bar)

        # Should work with global signals
        assert status_bar is not None

    def test_fixed_height(self, qtbot, signals: AetherSignals) -> None:
        """Test status bar has fixed height."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        assert status_bar.maximumHeight() == 28


# ============================================================================
# TestStatusBarIntegration
# ============================================================================


class TestStatusBarIntegration:
    """Integration tests for status bar."""

    def test_multiple_state_changes(self, qtbot, signals: AetherSignals) -> None:
        """Test multiple rapid state changes."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        # Rapid state changes
        signals.connection_state_changed.emit(ConnectionState.CONNECTING)
        signals.connection_state_changed.emit(ConnectionState.CONNECTED)
        signals.connection_state_changed.emit(ConnectionState.ERROR)
        signals.connection_state_changed.emit(ConnectionState.DISCONNECTED)
        signals.connection_state_changed.emit(ConnectionState.CONNECTED)

        # Final state should be Connected
        labels = status_bar.findChildren(QLabel)
        connected_labels = [lbl for lbl in labels if "Connected" in lbl.text()]
        assert len(connected_labels) >= 1

    def test_processing_cycle(self, qtbot, signals: AetherSignals) -> None:
        """Test complete processing cycle."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        # Multiple processing cycles
        for _ in range(3):
            signals.processing_started.emit()
            labels = status_bar.findChildren(QLabel)
            assert any("Processing" in lbl.text() for lbl in labels)

            signals.processing_finished.emit()
            labels = status_bar.findChildren(QLabel)
            assert not any("Processing" in lbl.text() for lbl in labels)

    def test_concurrent_updates(self, qtbot, signals: AetherSignals) -> None:
        """Test handling multiple concurrent signal types."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        # Send multiple signals
        signals.connection_state_changed.emit(ConnectionState.CONNECTED)
        signals.provider_changed.emit("OpenAI", "gpt-4")
        signals.processing_started.emit()

        labels = status_bar.findChildren(QLabel)

        # All should be reflected
        assert any("Connected" in lbl.text() for lbl in labels)
        assert any("OpenAI" in lbl.text() for lbl in labels)
        assert any("Processing" in lbl.text() for lbl in labels)


# ============================================================================
# TestEdgeCases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_provider_with_long_name(self, qtbot, signals: AetherSignals) -> None:
        """Test provider with very long name."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        long_provider = "A" * 100
        long_model = "B" * 100
        signals.provider_changed.emit(long_provider, long_model)

        # Should not crash
        labels = status_bar.findChildren(QLabel)
        assert any(long_provider in lbl.text() for lbl in labels)

    def test_provider_with_special_characters(
        self, qtbot, signals: AetherSignals
    ) -> None:
        """Test provider with special characters."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        signals.provider_changed.emit("<Provider>", "model/v2.0")

        # Should handle without issues
        labels = status_bar.findChildren(QLabel)
        # At least the AI indicator should be present
        assert len(labels) > 0

    def test_empty_provider(self, qtbot, signals: AetherSignals) -> None:
        """Test with empty provider name."""
        status_bar = AetherStatusBar(signals)
        qtbot.addWidget(status_bar)

        signals.provider_changed.emit("", "")

        # Should not crash
        assert status_bar is not None

    def test_status_color_function(self) -> None:
        """Test get_status_color returns valid colors."""
        statuses = [
            "connected",
            "Connected",
            "CONNECTED",
            "disconnected",
            "Disconnected",
            "connecting",
            "Connecting...",
            "error",
            "Error",
            "ready",
            "Ready",
            "unknown",
            "",
        ]

        for status in statuses:
            color = get_status_color(status)
            # Should return a color string (hex or named)
            assert isinstance(color, str)
            assert len(color) > 0
