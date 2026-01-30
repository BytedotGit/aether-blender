"""
Unit Tests for GUI Settings Dialog Module.

Tests for SettingsDialog class and provider/model configuration.
"""

import pytest
from PyQt6.QtWidgets import QComboBox, QGroupBox, QLineEdit, QPushButton

from src.gui.settings_dialog import (
    DEFAULT_MODELS,
    DEFAULT_PROVIDER,
    PROVIDER_MODELS,
    SettingsDialog,
)
from src.gui.signals import AetherSignals, get_signals, reset_signals

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
# TestSettingsDialogCreation
# ============================================================================


class TestSettingsDialogCreation:
    """Tests for SettingsDialog creation and initialization."""

    def test_dialog_creation(self, qtbot, signals: AetherSignals) -> None:
        """Test SettingsDialog can be created."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        assert dialog is not None

    def test_dialog_has_title(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has correct title."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Settings"

    def test_dialog_minimum_width(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has minimum width."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        assert dialog.minimumWidth() >= 450

    def test_default_provider(self, qtbot, signals: AetherSignals) -> None:
        """Test default provider is set correctly."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        assert dialog.current_provider == DEFAULT_PROVIDER

    def test_default_model(self, qtbot, signals: AetherSignals) -> None:
        """Test default model is set correctly."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        assert dialog.current_model == DEFAULT_MODELS[DEFAULT_PROVIDER]

    def test_default_signals_used(self, qtbot) -> None:
        """Test default signals are used if none provided."""
        dialog = SettingsDialog()  # No signals argument
        qtbot.addWidget(dialog)

        assert dialog is not None


# ============================================================================
# TestSettingsDialogUI
# ============================================================================


class TestSettingsDialogUI:
    """Tests for SettingsDialog UI components."""

    def test_has_ai_provider_section(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has AI Provider section."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        groups = dialog.findChildren(QGroupBox)
        ai_groups = [g for g in groups if "AI" in g.title()]
        assert len(ai_groups) >= 1

    def test_has_connection_section(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has Connection section."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        groups = dialog.findChildren(QGroupBox)
        conn_groups = [g for g in groups if "Connection" in g.title()]
        assert len(conn_groups) >= 1

    def test_has_provider_combo(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has provider combobox."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        combos = dialog.findChildren(QComboBox)
        assert len(combos) >= 1

    def test_has_model_combo(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has model combobox."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        combos = dialog.findChildren(QComboBox)
        assert len(combos) >= 2  # Provider and Model

    def test_has_api_key_input(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has API key input."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        line_edits = dialog.findChildren(QLineEdit)
        # Should have API key, host, and port inputs
        assert len(line_edits) >= 3

    def test_has_host_input(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has host input with default value."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        line_edits = dialog.findChildren(QLineEdit)
        host_inputs = [le for le in line_edits if le.text() == "localhost"]
        assert len(host_inputs) >= 1

    def test_has_port_input(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has port input with default value."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        line_edits = dialog.findChildren(QLineEdit)
        port_inputs = [le for le in line_edits if le.text() == "5005"]
        assert len(port_inputs) >= 1

    def test_has_save_button(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has save button."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        buttons = dialog.findChildren(QPushButton)
        save_buttons = [b for b in buttons if b.text() == "Save"]
        assert len(save_buttons) >= 1

    def test_has_cancel_button(self, qtbot, signals: AetherSignals) -> None:
        """Test dialog has cancel button."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        buttons = dialog.findChildren(QPushButton)
        cancel_buttons = [b for b in buttons if b.text() == "Cancel"]
        assert len(cancel_buttons) >= 1

    def test_api_key_password_mode(self, qtbot, signals: AetherSignals) -> None:
        """Test API key input is in password mode."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        line_edits = dialog.findChildren(QLineEdit)
        password_inputs = [
            le for le in line_edits if le.echoMode() == QLineEdit.EchoMode.Password
        ]
        assert len(password_inputs) >= 1


# ============================================================================
# TestProviderModels
# ============================================================================


class TestProviderModels:
    """Tests for provider and model configuration."""

    def test_all_providers_in_combo(self, qtbot, signals: AetherSignals) -> None:
        """Test all providers are available in combobox."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        combos = dialog.findChildren(QComboBox)
        provider_combo = combos[0]  # First combo is provider

        items = [provider_combo.itemData(i) for i in range(provider_combo.count())]
        for provider in PROVIDER_MODELS:
            assert provider in items

    def test_provider_change_updates_models(
        self, qtbot, signals: AetherSignals
    ) -> None:
        """Test changing provider updates model dropdown."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        combos = dialog.findChildren(QComboBox)
        provider_combo = combos[0]
        model_combo = combos[1]

        # Change to openai
        openai_idx = provider_combo.findData("openai")
        provider_combo.setCurrentIndex(openai_idx)

        # Model combo should have openai models
        model_items = [model_combo.itemData(i) for i in range(model_combo.count())]
        for model in PROVIDER_MODELS["openai"]:
            assert model in model_items

    def test_set_provider_method(self, qtbot, signals: AetherSignals) -> None:
        """Test set_provider method sets correct provider and model."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        dialog.set_provider("anthropic", "claude-3-opus-20240229")

        combos = dialog.findChildren(QComboBox)
        provider_combo = combos[0]
        model_combo = combos[1]

        assert provider_combo.currentData() == "anthropic"
        assert model_combo.currentData() == "claude-3-opus-20240229"

    def test_default_model_selected(self, qtbot, signals: AetherSignals) -> None:
        """Test default model is selected when provider changes."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        combos = dialog.findChildren(QComboBox)
        provider_combo = combos[0]
        model_combo = combos[1]

        # Change to openai
        openai_idx = provider_combo.findData("openai")
        provider_combo.setCurrentIndex(openai_idx)

        # Default model for openai should be selected
        assert model_combo.currentData() == DEFAULT_MODELS["openai"]


# ============================================================================
# TestSettingsDialogActions
# ============================================================================


class TestSettingsDialogActions:
    """Tests for SettingsDialog actions."""

    def test_save_emits_signals(self, qtbot, signals: AetherSignals) -> None:
        """Test save button emits settings_changed and provider_changed signals."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        settings_received = []
        provider_received = []

        signals.settings_changed.connect(lambda s: settings_received.append(s))
        signals.provider_changed.connect(lambda p, m: provider_received.append((p, m)))

        # Click save
        buttons = dialog.findChildren(QPushButton)
        save_btn = next(b for b in buttons if b.text() == "Save")
        save_btn.click()

        assert len(settings_received) == 1
        assert len(provider_received) == 1

    def test_save_settings_content(self, qtbot, signals: AetherSignals) -> None:
        """Test saved settings contain correct data."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        settings_received = []
        signals.settings_changed.connect(lambda s: settings_received.append(s))

        # Click save
        buttons = dialog.findChildren(QPushButton)
        save_btn = next(b for b in buttons if b.text() == "Save")
        save_btn.click()

        settings = settings_received[0]
        assert "provider" in settings
        assert "model" in settings
        assert "host" in settings
        assert "port" in settings

    def test_save_with_custom_values(self, qtbot, signals: AetherSignals) -> None:
        """Test save with custom provider and model."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        # Change provider to openai
        dialog.set_provider("openai", "gpt-4")

        provider_received = []
        signals.provider_changed.connect(lambda p, m: provider_received.append((p, m)))

        # Click save
        buttons = dialog.findChildren(QPushButton)
        save_btn = next(b for b in buttons if b.text() == "Save")
        save_btn.click()

        assert provider_received[0] == ("openai", "gpt-4")

    def test_cancel_closes_dialog(self, qtbot, signals: AetherSignals) -> None:
        """Test cancel button closes dialog without saving."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        settings_received = []
        signals.settings_changed.connect(lambda s: settings_received.append(s))

        # Click cancel
        buttons = dialog.findChildren(QPushButton)
        cancel_btn = next(b for b in buttons if b.text() == "Cancel")
        cancel_btn.click()

        # No settings should be emitted
        assert len(settings_received) == 0

    def test_save_updates_current_provider(self, qtbot, signals: AetherSignals) -> None:
        """Test save updates current_provider property."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        # Change provider
        dialog.set_provider("anthropic", "claude-sonnet-4-20250514")

        # Click save
        buttons = dialog.findChildren(QPushButton)
        save_btn = next(b for b in buttons if b.text() == "Save")
        save_btn.click()

        assert dialog.current_provider == "anthropic"
        assert dialog.current_model == "claude-sonnet-4-20250514"


# ============================================================================
# TestProviderModelConstants
# ============================================================================


class TestProviderModelConstants:
    """Tests for provider/model constants."""

    def test_provider_models_not_empty(self) -> None:
        """Test PROVIDER_MODELS is not empty."""
        assert len(PROVIDER_MODELS) > 0

    def test_all_providers_have_models(self) -> None:
        """Test all providers have at least one model."""
        for provider, models in PROVIDER_MODELS.items():
            assert len(models) > 0, f"Provider {provider} has no models"

    def test_default_models_exist(self) -> None:
        """Test default models exist for all providers."""
        for provider in PROVIDER_MODELS:
            assert provider in DEFAULT_MODELS
            default_model = DEFAULT_MODELS[provider]
            assert default_model in PROVIDER_MODELS[provider]

    def test_default_provider_valid(self) -> None:
        """Test default provider is valid."""
        assert DEFAULT_PROVIDER in PROVIDER_MODELS


# ============================================================================
# TestEdgeCases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_invalid_provider_set(self, qtbot, signals: AetherSignals) -> None:
        """Test setting invalid provider does not crash."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        # Should not crash
        dialog.set_provider("invalid_provider", "invalid_model")

    def test_empty_model_list(self, qtbot, signals: AetherSignals) -> None:
        """Test handling of provider with no models (edge case)."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        # Should handle gracefully even if models list were empty
        combos = dialog.findChildren(QComboBox)
        model_combo = combos[1]
        assert model_combo is not None

    def test_rapid_provider_changes(self, qtbot, signals: AetherSignals) -> None:
        """Test rapid provider changes don't cause issues."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        combos = dialog.findChildren(QComboBox)
        provider_combo = combos[0]

        # Rapidly change providers
        for _ in range(20):
            for i in range(provider_combo.count()):
                provider_combo.setCurrentIndex(i)

        # Should not crash

    def test_special_characters_in_host(self, qtbot, signals: AetherSignals) -> None:
        """Test special characters in host input."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        line_edits = dialog.findChildren(QLineEdit)
        host_input = next(le for le in line_edits if le.text() == "localhost")
        host_input.setText("192.168.1.100")

        settings_received = []
        signals.settings_changed.connect(lambda s: settings_received.append(s))

        buttons = dialog.findChildren(QPushButton)
        save_btn = next(b for b in buttons if b.text() == "Save")
        save_btn.click()

        assert settings_received[0]["host"] == "192.168.1.100"

    def test_custom_port(self, qtbot, signals: AetherSignals) -> None:
        """Test custom port value."""
        dialog = SettingsDialog(signals)
        qtbot.addWidget(dialog)

        line_edits = dialog.findChildren(QLineEdit)
        port_input = next(le for le in line_edits if le.text() == "5005")
        port_input.setText("9999")

        settings_received = []
        signals.settings_changed.connect(lambda s: settings_received.append(s))

        buttons = dialog.findChildren(QPushButton)
        save_btn = next(b for b in buttons if b.text() == "Save")
        save_btn.click()

        assert settings_received[0]["port"] == "9999"
