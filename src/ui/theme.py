APP_BG = "#eef4fb"
CARD_BG = "#ffffff"
CARD_BORDER = "#cbd5e1"
HEADER_BLUE = "#0b3970"
HEADER_BLUE_DARK = "#082f61"
TEXT = "#111827"
MUTED = "#475569"
LIGHT_BLUE = "#f1f8ff"
LIGHT_GREEN = "#f1fbf3"
LIGHT_YELLOW = "#fff8e6"
TABLE_HEADER = "#eef3fb"
PRIMARY_BLUE = "#1558b0"
SUCCESS_GREEN = "#168033"
WARNING_YELLOW = "#d99a15"
DANGER_RED = "#dc2626"
OUTLINE_BLUE = "#0b3970"


def button_style(kind="primary"):
    styles = {
        "primary": {"fg_color": PRIMARY_BLUE, "hover_color": "#0f4a98", "text_color": "white"},
        "success": {"fg_color": SUCCESS_GREEN, "hover_color": "#116b2a", "text_color": "white"},
        "warning": {"fg_color": WARNING_YELLOW, "hover_color": "#bf8411", "text_color": "#111827"},
        "danger": {"fg_color": DANGER_RED, "hover_color": "#b91c1c", "text_color": "white"},
        "outline": {
            "fg_color": CARD_BG,
            "hover_color": "#e0f2fe",
            "text_color": OUTLINE_BLUE,
            "border_width": 1,
            "border_color": "#8aa9d6",
        },
        "quick": {
            "fg_color": CARD_BG,
            "hover_color": "#fff1c2",
            "text_color": TEXT,
            "border_width": 1,
            "border_color": "#f0c36a",
        },
    }
    return styles[kind]
