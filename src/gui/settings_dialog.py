"""
Aether Settings Dialog Module.

Configuration dialog for AI provider and model selection.
"""

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.gui.signals import AetherSignals, get_signals
from src.gui.styles import COLORS, DIMS, FONTS, get_full_stylesheet
from src.telemetry.logger import get_logger

logger = get_logger(__name__)


# Available providers and their models
PROVIDER_MODELS = {
    "gemini": [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro",
    ],
    "openai": [
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
    ],
    "anthropic": [
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20240620",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ],
}

DEFAULT_PROVIDER = "gemini"
DEFAULT_MODELS = {
    "gemini": "gemini-2.0-flash",
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
}


class SettingsDialog(QDialog):
    """
    Settings dialog for configuring AI provider and other options.
    """

    def __init__(
        self,
        signals: AetherSignals | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize settings dialog.

        Args:
            signals: AetherSignals instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._signals = signals or get_signals()
        self._current_provider = DEFAULT_PROVIDER
        self._current_model = DEFAULT_MODELS[DEFAULT_PROVIDER]
        self._setup_ui()
        logger.debug("SettingsDialog initialized")

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self.setStyleSheet(get_full_stylesheet())

        layout = QVBoxLayout(self)
        layout.setSpacing(DIMS.spacing_lg)
        layout.setContentsMargins(
            DIMS.spacing_lg, DIMS.spacing_lg, DIMS.spacing_lg, DIMS.spacing_lg
        )

        # AI Provider section
        ai_group = self._create_ai_section()
        layout.addWidget(ai_group)

        # Connection section
        conn_group = self._create_connection_section()
        layout.addWidget(conn_group)

        layout.addStretch()

        # Buttons
        buttons = self._create_buttons()
        layout.addLayout(buttons)

    def _create_ai_section(self) -> QGroupBox:
        """Create AI provider configuration section."""
        group = QGroupBox("AI Provider")
        group.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS.border_medium};
                border-radius: {DIMS.radius_md}px;
                margin-top: 16px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
        """
        )

        layout = QFormLayout(group)
        layout.setSpacing(DIMS.spacing_md)
        layout.setContentsMargins(
            DIMS.spacing_md, DIMS.spacing_lg, DIMS.spacing_md, DIMS.spacing_md
        )

        # Provider dropdown
        self._provider_combo = QComboBox()
        for provider in PROVIDER_MODELS:
            self._provider_combo.addItem(provider.capitalize(), provider)
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        layout.addRow("Provider:", self._provider_combo)

        # Model dropdown
        self._model_combo = QComboBox()
        self._update_models(DEFAULT_PROVIDER)
        layout.addRow("Model:", self._model_combo)

        # API Key input
        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setPlaceholderText("Enter API key (stored in .env)")
        layout.addRow("API Key:", self._api_key_input)

        # Status label
        self._status_label = QLabel("Using key from environment")
        self._status_label.setStyleSheet(
            f"color: {COLORS.text_muted}; font-size: {FONTS.size_small}px;"
        )
        layout.addRow("", self._status_label)

        return group

    def _create_connection_section(self) -> QGroupBox:
        """Create Blender connection configuration section."""
        group = QGroupBox("Blender Connection")
        group.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS.border_medium};
                border-radius: {DIMS.radius_md}px;
                margin-top: 16px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
        """
        )

        layout = QFormLayout(group)
        layout.setSpacing(DIMS.spacing_md)
        layout.setContentsMargins(
            DIMS.spacing_md, DIMS.spacing_lg, DIMS.spacing_md, DIMS.spacing_md
        )

        # Host
        self._host_input = QLineEdit("localhost")
        layout.addRow("Host:", self._host_input)

        # Port
        self._port_input = QLineEdit("5005")
        self._port_input.setMaximumWidth(100)
        layout.addRow("Port:", self._port_input)

        return group

    def _create_buttons(self) -> QHBoxLayout:
        """Create dialog buttons."""
        layout = QHBoxLayout()
        layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(80)
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

        return layout

    def _on_provider_changed(self, _index: int) -> None:
        """Handle provider selection change."""
        provider = self._provider_combo.currentData()
        if provider:
            self._current_provider = provider
            self._update_models(provider)
            logger.debug("Provider changed", extra={"provider": provider})

    def _update_models(self, provider: str) -> None:
        """Update model dropdown for selected provider."""
        self._model_combo.clear()
        models = PROVIDER_MODELS.get(provider, [])
        for model in models:
            self._model_combo.addItem(model, model)

        # Select default model
        default = DEFAULT_MODELS.get(provider, models[0] if models else "")
        idx = self._model_combo.findData(default)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)

    def _on_save(self) -> None:
        """Handle save button click."""
        provider = self._provider_combo.currentData()
        model = self._model_combo.currentData()

        if provider and model:
            self._current_provider = provider
            self._current_model = model

            # Emit settings changed
            settings = {
                "provider": provider,
                "model": model,
                "host": self._host_input.text(),
                "port": self._port_input.text(),
            }

            logger.info(
                "Settings saved",
                extra={"provider": provider, "model": model},
            )

            self._signals.settings_changed.emit(settings)
            self._signals.provider_changed.emit(provider, model)

        self.accept()

    def set_provider(self, provider: str, model: str) -> None:
        """
        Set the current provider and model.

        Args:
            provider: Provider name
            model: Model name
        """
        idx = self._provider_combo.findData(provider)
        if idx >= 0:
            self._provider_combo.setCurrentIndex(idx)
            self._update_models(provider)

            model_idx = self._model_combo.findData(model)
            if model_idx >= 0:
                self._model_combo.setCurrentIndex(model_idx)

    @property
    def current_provider(self) -> str:
        """Return current provider."""
        return self._current_provider

    @property
    def current_model(self) -> str:
        """Return current model."""
        return self._current_model
