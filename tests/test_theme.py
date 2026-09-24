from src.ui import theme


def test_picks_first_installed_candidate():
    assert theme.pick_font_family(["Arial", "Gill Sans MT", "Cabin"], theme.TITLE_FONT_CANDIDATES) == "Gill Sans MT"


def test_falls_back_to_next_candidate_when_first_is_missing():
    assert theme.pick_font_family(["Arial", "Cabin"], theme.TITLE_FONT_CANDIDATES) == "Cabin"


def test_font_names_are_compared_ignoring_case():
    assert theme.pick_font_family(["gill sans mt"], theme.TITLE_FONT_CANDIDATES) == "Gill Sans MT"


def test_uses_fallback_when_no_candidate_is_installed():
    assert theme.pick_font_family(["Comic Sans"], theme.TITLE_FONT_CANDIDATES, "Segoe UI") == "Segoe UI"


def test_action_buttons_never_use_white_text_on_pure_orange():
    for kind in ("primary", "success", "cta", "danger", "outline", "warning", "quick", "muted"):
        style = theme.button_style(kind)
        assert not (style["fg_color"].upper() == theme.ORANGE and style["text_color"].upper() == "#FFFFFF"), kind


def _luminance(hex_color):
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first, second):
    high, low = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_filled_buttons_have_readable_contrast():
    for kind in ("primary", "success", "cta", "danger", "muted"):
        style = theme.button_style(kind)
        assert _contrast(style["fg_color"], style["text_color"]) >= 4.5, kind


def test_text_colors_are_readable_on_cards():
    assert _contrast(theme.TEXT, theme.CARD_BG) >= 7
    assert _contrast(theme.MUTED, theme.CARD_BG) >= 4.5
    assert _contrast(theme.WARNING_TEXT, theme.WARNING_TINT) >= 4.5
    assert _contrast(theme.ORANGE_DARK, theme.CARD_BG) >= 4.5
