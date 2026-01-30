"""
Tests for GUI Styles Module.

Tests the styling constants and stylesheet generation.
"""

from src.gui.styles import (
    COLORS,
    DIMS,
    FONTS,
    ColorPalette,
    Dimensions,
    FontConfig,
    get_base_stylesheet,
    get_chat_stylesheet,
    get_full_stylesheet,
    get_status_color,
    get_toast_stylesheet,
)


class TestColorPalette:
    """Test ColorPalette dataclass."""

    def test_colors_instance_exists(self) -> None:
        """Test COLORS instance is available."""
        assert COLORS is not None
        assert isinstance(COLORS, ColorPalette)

    def test_primary_color_format(self) -> None:
        """Test primary color is valid hex format."""
        assert COLORS.primary.startswith("#")
        assert len(COLORS.primary) == 7

    def test_status_colors_exist(self) -> None:
        """Test status colors are defined."""
        assert COLORS.success is not None
        assert COLORS.warning is not None
        assert COLORS.error is not None
        assert COLORS.info is not None

    def test_background_colors_exist(self) -> None:
        """Test background colors are defined."""
        assert COLORS.bg_dark is not None
        assert COLORS.bg_medium is not None
        assert COLORS.bg_light is not None

    def test_text_colors_exist(self) -> None:
        """Test text colors are defined."""
        assert COLORS.text_primary is not None
        assert COLORS.text_secondary is not None
        assert COLORS.text_muted is not None

    def test_bubble_colors_exist(self) -> None:
        """Test message bubble colors are defined."""
        assert COLORS.user_bubble is not None
        assert COLORS.assistant_bubble is not None
        assert COLORS.system_bubble is not None
        assert COLORS.error_bubble is not None


class TestFontConfig:
    """Test FontConfig dataclass."""

    def test_fonts_instance_exists(self) -> None:
        """Test FONTS instance is available."""
        assert FONTS is not None
        assert isinstance(FONTS, FontConfig)

    def test_font_families_exist(self) -> None:
        """Test font families are defined."""
        assert FONTS.family_default is not None
        assert FONTS.family_mono is not None

    def test_font_sizes_exist(self) -> None:
        """Test font sizes are defined."""
        assert FONTS.size_small > 0
        assert FONTS.size_normal > 0
        assert FONTS.size_large > 0

    def test_font_sizes_ordered(self) -> None:
        """Test font sizes are in ascending order."""
        assert FONTS.size_small < FONTS.size_normal
        assert FONTS.size_normal < FONTS.size_large
        assert FONTS.size_large < FONTS.size_title


class TestDimensions:
    """Test Dimensions dataclass."""

    def test_dims_instance_exists(self) -> None:
        """Test DIMS instance is available."""
        assert DIMS is not None
        assert isinstance(DIMS, Dimensions)

    def test_spacing_values_exist(self) -> None:
        """Test spacing values are defined."""
        assert DIMS.spacing_xs > 0
        assert DIMS.spacing_sm > 0
        assert DIMS.spacing_md > 0
        assert DIMS.spacing_lg > 0

    def test_spacing_values_ordered(self) -> None:
        """Test spacing values are in ascending order."""
        assert DIMS.spacing_xs < DIMS.spacing_sm
        assert DIMS.spacing_sm < DIMS.spacing_md
        assert DIMS.spacing_md < DIMS.spacing_lg

    def test_radius_values_exist(self) -> None:
        """Test border radius values are defined."""
        assert DIMS.radius_sm > 0
        assert DIMS.radius_md > 0
        assert DIMS.radius_lg > 0

    def test_touch_target_minimum(self) -> None:
        """Test minimum touch target meets accessibility guidelines."""
        assert DIMS.min_touch_target >= 44


class TestStylesheetGeneration:
    """Test stylesheet generation functions."""

    def test_get_base_stylesheet_returns_string(self) -> None:
        """Test base stylesheet returns a string."""
        stylesheet = get_base_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_base_stylesheet_contains_qwidget(self) -> None:
        """Test base stylesheet contains QWidget styles."""
        stylesheet = get_base_stylesheet()
        assert "QWidget" in stylesheet

    def test_base_stylesheet_contains_colors(self) -> None:
        """Test base stylesheet contains color values."""
        stylesheet = get_base_stylesheet()
        assert COLORS.bg_dark in stylesheet

    def test_get_chat_stylesheet_returns_string(self) -> None:
        """Test chat stylesheet returns a string."""
        stylesheet = get_chat_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_chat_stylesheet_contains_bubbles(self) -> None:
        """Test chat stylesheet contains bubble styles."""
        stylesheet = get_chat_stylesheet()
        assert "userBubble" in stylesheet
        assert "assistantBubble" in stylesheet

    def test_get_toast_stylesheet_returns_string(self) -> None:
        """Test toast stylesheet returns a string."""
        stylesheet = get_toast_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_toast_stylesheet_contains_variants(self) -> None:
        """Test toast stylesheet contains toast variants."""
        stylesheet = get_toast_stylesheet()
        assert "toastInfo" in stylesheet
        assert "toastSuccess" in stylesheet
        assert "toastError" in stylesheet

    def test_get_full_stylesheet_combines_all(self) -> None:
        """Test full stylesheet combines all stylesheets."""
        full = get_full_stylesheet()
        base = get_base_stylesheet()

        # Verify key elements from each stylesheet are present
        assert base in full or "QWidget" in full
        assert "userBubble" in full  # from chat stylesheet
        assert "toastInfo" in full  # from toast stylesheet


class TestGetStatusColor:
    """Test get_status_color function."""

    def test_connected_returns_success_color(self) -> None:
        """Test connected status returns success color."""
        color = get_status_color("connected")
        assert color == COLORS.success

    def test_disconnected_returns_error_color(self) -> None:
        """Test disconnected status returns error color."""
        color = get_status_color("disconnected")
        assert color == COLORS.error

    def test_connecting_returns_warning_color(self) -> None:
        """Test connecting status returns warning color."""
        color = get_status_color("connecting")
        assert color == COLORS.warning

    def test_unknown_returns_muted_color(self) -> None:
        """Test unknown status returns muted color."""
        color = get_status_color("unknown")
        assert color == COLORS.text_muted

    def test_case_insensitive(self) -> None:
        """Test status lookup is case insensitive."""
        assert get_status_color("CONNECTED") == COLORS.success
        assert get_status_color("Connected") == COLORS.success
