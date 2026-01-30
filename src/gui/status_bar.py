"""
Aether Status Bar Module.

Status bar for displaying connection state, Blender status, and other info.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from src.gui.signals import AetherSignals, ConnectionState, get_signals
from src.gui.styles import COLORS, DIMS, FONTS, get_status_color
from src.telemetry.logger import get_logger

logger = get_logger(__name__)


class StatusIndicator(QFrame):
    """
    Status indicator widget with icon and text.

    Displays a colored indicator with label.
    """

    def __init__(
        self,
        label: str,
        status: str = "disconnected",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize status indicator.

        Args:
            label: Display label
            status: Initial status string
            parent: Parent widget
        """
        super().__init__(parent)
        self._label = label
        self._status = status
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the indicator UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(DIMS.spacing_sm, 0, DIMS.spacing_sm, 0)
        layout.setSpacing(DIMS.spacing_xs)

        # Status dot
        self._dot = QLabel("●")
        self._dot.setFixedWidth(16)
        self._dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._dot)

        # Label
        self._text = QLabel(f"{self._label}: {self._status}")
        self._text.setStyleSheet(
            f"color: {COLORS.text_secondary}; font-size: {FONTS.size_small}px;"
        )
        layout.addWidget(self._text)

        self._update_color()

    def set_status(self, status: str) -> None:
        """Update the status."""
        self._status = status
        self._text.setText(f"{self._label}: {status}")
        self._update_color()
        logger.debug(
            "Status indicator updated",
            extra={"label": self._label, "status": status},
        )

    def _update_color(self) -> None:
        """Update the dot color based on status."""
        color = get_status_color(self._status)
        self._dot.setStyleSheet(f"color: {color};")


class AetherStatusBar(QFrame):
    """
    Application status bar.

    Displays:
    - Blender connection status
    - Current AI provider
    - Processing state
    """

    def __init__(
        self,
        signals: AetherSignals | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize status bar.

        Args:
            signals: AetherSignals instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._signals = signals or get_signals()
        self._setup_ui()
        self._connect_signals()
        logger.debug("AetherStatusBar initialized")

    def _setup_ui(self) -> None:
        """Set up the status bar UI."""
        self.setFixedHeight(28)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {COLORS.bg_medium};
                border-top: 1px solid {COLORS.border_dark};
            }}
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(DIMS.spacing_md, 0, DIMS.spacing_md, 0)
        layout.setSpacing(DIMS.spacing_lg)

        # Blender connection status
        self._blender_status = StatusIndicator("Blender", "Disconnected", self)
        layout.addWidget(self._blender_status)

        # Separator
        sep1 = QLabel("|")
        sep1.setStyleSheet(f"color: {COLORS.border_medium};")
        layout.addWidget(sep1)

        # AI provider status
        self._ai_status = StatusIndicator("AI", "Ready", self)
        layout.addWidget(self._ai_status)

        # Separator
        sep2 = QLabel("|")
        sep2.setStyleSheet(f"color: {COLORS.border_medium};")
        layout.addWidget(sep2)

        # Processing indicator
        self._processing_label = QLabel("")
        self._processing_label.setStyleSheet(
            f"color: {COLORS.text_muted}; font-size: {FONTS.size_small}px;"
        )
        layout.addWidget(self._processing_label)

        layout.addStretch()

        # Version info
        version_label = QLabel("Aether v0.1.0")
        version_label.setStyleSheet(
            f"color: {COLORS.text_muted}; font-size: {FONTS.size_small}px;"
        )
        layout.addWidget(version_label)

    def _connect_signals(self) -> None:
        """Connect to application signals."""
        self._signals.connection_state_changed.connect(self._on_connection_changed)
        self._signals.provider_changed.connect(self._on_provider_changed)
        self._signals.processing_started.connect(self._on_processing_started)
        self._signals.processing_finished.connect(self._on_processing_finished)

    def _on_connection_changed(self, state: ConnectionState) -> None:
        """Handle connection state change."""
        status_map = {
            ConnectionState.CONNECTED: "Connected",
            ConnectionState.DISCONNECTED: "Disconnected",
            ConnectionState.CONNECTING: "Connecting...",
            ConnectionState.ERROR: "Error",
        }
        self._blender_status.set_status(status_map.get(state, "Unknown"))

    def _on_provider_changed(self, provider: str, model: str) -> None:
        """Handle AI provider change."""
        self._ai_status.set_status(f"{provider} ({model})")

    def _on_processing_started(self) -> None:
        """Handle processing started."""
        self._processing_label.setText("⏳ Processing...")
        self._processing_label.setStyleSheet(
            f"color: {COLORS.warning}; font-size: {FONTS.size_small}px;"
        )

    def _on_processing_finished(self) -> None:
        """Handle processing finished."""
        self._processing_label.setText("")
