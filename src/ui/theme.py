"""Identidade visual da Uniartes Uniformes (ver docs/brand.md).

Regra de contraste: branco sobre o laranja puro (#F47726) reprova (2,8:1). Botões de ação usam grafite ou o laranja
escuro derivado (#B95A1D, 4,6:1 com branco); o laranja puro fica para destaques, ícones e barras.
"""
import tkinter.font as tkfont

import customtkinter as ctk

# --- Marca ---
GRAPHITE = "#454849"
GRAPHITE_DARK = "#343637"
GRAPHITE_SOFT = "#5C6062"
ORANGE = "#F47726"
ORANGE_DARK = "#B95A1D"
ORANGE_DARKER = "#9A4A16"
ORANGE_TINT = "#FDEEE3"

# --- Superfícies e texto ---
APP_BG = "#F4F5F5"
SURFACE_ALT = "#F8F9F9"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#D9DCDD"
FIELD_BORDER = "#B8BDBE"
TEXT = "#2C2F30"
MUTED = "#6B7071"
ON_DARK = "#FFFFFF"
ON_DARK_MUTED = "#D9DCDD"

# --- Estados funcionais ---
SUCCESS_GREEN = "#2E7D32"
SUCCESS_TINT = "#EEF7EF"
SUCCESS_BORDER = "#8CC08F"
DANGER_RED = "#B3261E"
DANGER_DARK = "#8C1D18"
WARNING_TEXT = ORANGE_DARKER  # texto sobre o fundo laranja claro (contraste >= 4,5:1)
WARNING_TINT = ORANGE_TINT
WARNING_BORDER = ORANGE

# --- Nomes antigos (mantidos para não quebrar imports) ---
HEADER_BLUE = GRAPHITE
HEADER_BLUE_DARK = GRAPHITE_DARK
LIGHT_BLUE = CARD_BG
LIGHT_GREEN = CARD_BG
LIGHT_YELLOW = CARD_BG
TABLE_HEADER = GRAPHITE
PRIMARY_BLUE = GRAPHITE
WARNING_YELLOW = ORANGE_DARK
OUTLINE_BLUE = GRAPHITE

# O Gill Sans MT (da marca) tem o algarismo 1 parecido com a letra I, ruim para números de pedido e quantidades.
# Por isso ele fica só nos títulos; o texto do dia a dia usa a fonte padrão do Windows.
BASE_FONT_CANDIDATES = ("Segoe UI", "Arial")
TITLE_FONT_CANDIDATES = ("Gill Sans MT", "Cabin")
FALLBACK_FONT = "Arial"
BASE_FONT_SIZE = 13

_font_family = "Segoe UI"
_title_family = "Segoe UI"


def font_family():
    return _font_family


def pick_font_family(available, candidates, fallback=FALLBACK_FONT):
    """Primeira fonte da lista que esteja instalada na máquina; senão a de reserva."""
    installed = {name.casefold() for name in available}
    for candidate in candidates:
        if candidate.casefold() in installed:
            return candidate
    return fallback


def apply_brand_theme(root):
    """Ajusta o tema do customtkinter (cores e fonte) antes de criar qualquer widget."""
    global _font_family, _title_family
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    families = tkfont.families(root)
    _font_family = pick_font_family(families, BASE_FONT_CANDIDATES)
    _title_family = pick_font_family(families, TITLE_FONT_CANDIDATES, _font_family)
    theme = ctk.ThemeManager.theme

    theme["CTkFont"] = {"family": _font_family, "size": BASE_FONT_SIZE, "weight": "normal"}
    theme["CTk"]["fg_color"] = [APP_BG, APP_BG]
    theme["CTkToplevel"]["fg_color"] = [APP_BG, APP_BG]
    theme["CTkFrame"].update(fg_color=[CARD_BG, CARD_BG], border_color=[CARD_BORDER, CARD_BORDER])
    theme["CTkLabel"]["text_color"] = [TEXT, TEXT]
    theme["CTkButton"].update(
        fg_color=[GRAPHITE, GRAPHITE],
        hover_color=[GRAPHITE_DARK, GRAPHITE_DARK],
        text_color=[ON_DARK, ON_DARK],
        border_color=[GRAPHITE, GRAPHITE],
        corner_radius=8,
    )
    theme["CTkCheckBox"].update(
        fg_color=[ORANGE_DARK, ORANGE_DARK],
        hover_color=[ORANGE_DARKER, ORANGE_DARKER],
        border_color=[FIELD_BORDER, FIELD_BORDER],
        checkmark_color=[ON_DARK, ON_DARK],
        text_color=[TEXT, TEXT],
        border_width=2,
    )
    theme["CTkOptionMenu"].update(
        fg_color=[GRAPHITE, GRAPHITE],
        button_color=[GRAPHITE_DARK, GRAPHITE_DARK],
        button_hover_color=[ORANGE_DARK, ORANGE_DARK],
        text_color=[ON_DARK, ON_DARK],
        corner_radius=8,
    )
    theme["DropdownMenu"] = {
        "fg_color": [CARD_BG, CARD_BG],
        "hover_color": [ORANGE_TINT, ORANGE_TINT],
        "text_color": [TEXT, TEXT],
    }
    theme["CTkEntry"].update(
        fg_color=[CARD_BG, CARD_BG],
        border_color=[FIELD_BORDER, FIELD_BORDER],
        text_color=[TEXT, TEXT],
        border_width=1,
        corner_radius=8,
    )
    theme["CTkTextbox"].update(
        fg_color=[CARD_BG, CARD_BG],
        border_color=[FIELD_BORDER, FIELD_BORDER],
        text_color=[TEXT, TEXT],
        scrollbar_button_color=[FIELD_BORDER, FIELD_BORDER],
        scrollbar_button_hover_color=[GRAPHITE_SOFT, GRAPHITE_SOFT],
    )
    theme["CTkProgressBar"].update(fg_color=[CARD_BORDER, CARD_BORDER], progress_color=[ORANGE, ORANGE])
    theme["CTkScrollbar"].update(
        button_color=[FIELD_BORDER, FIELD_BORDER], button_hover_color=[GRAPHITE_SOFT, GRAPHITE_SOFT]
    )
    theme["CTkScrollableFrame"] = {**theme.get("CTkScrollableFrame", {}), "label_fg_color": [CARD_BG, CARD_BG]}


def font(size=None, weight="normal", slant="roman", brand=False):
    family = _title_family if brand else _font_family
    return ctk.CTkFont(family=family, size=size or BASE_FONT_SIZE, weight=weight, slant=slant)


def button_style(kind="primary"):
    styles = {
        # Ação principal do dia a dia
        "primary": {"fg_color": GRAPHITE, "hover_color": GRAPHITE_DARK, "text_color": ON_DARK},
        # Ação que conclui o trabalho (gerar, salvar): laranja escuro, texto branco a 4,6:1
        "success": {"fg_color": ORANGE_DARK, "hover_color": ORANGE_DARKER, "text_color": ON_DARK},
        "cta": {"fg_color": ORANGE_DARK, "hover_color": ORANGE_DARKER, "text_color": ON_DARK},
        "warning": {
            "fg_color": ORANGE_TINT,
            "hover_color": "#FBDCC6",
            "text_color": TEXT,
            "border_width": 1,
            "border_color": ORANGE,
        },
        "danger": {"fg_color": DANGER_RED, "hover_color": DANGER_DARK, "text_color": ON_DARK},
        "outline": {
            "fg_color": CARD_BG,
            "hover_color": ORANGE_TINT,
            "text_color": GRAPHITE,
            "border_width": 1,
            "border_color": GRAPHITE,
        },
        "quick": {
            "fg_color": CARD_BG,
            "hover_color": ORANGE_TINT,
            "text_color": TEXT,
            "border_width": 1,
            "border_color": ORANGE,
        },
        "muted": {"fg_color": GRAPHITE_SOFT, "hover_color": GRAPHITE, "text_color": ON_DARK},
    }
    return styles[kind]


def apply_table_style(style):
    """Estilo do ttk.Treeview do carrinho."""
    style.configure(
        "Cart.Treeview",
        rowheight=32,
        font=(_font_family, 11),
        background=CARD_BG,
        fieldbackground=CARD_BG,
        foreground=TEXT,
        borderwidth=0,
    )
    style.configure(
        "Cart.Treeview.Heading",
        font=(_font_family, 11, "bold"),
        background=GRAPHITE,
        foreground=ON_DARK,
        relief="flat",
        padding=(6, 8),
    )
    style.map("Cart.Treeview.Heading", background=[("active", GRAPHITE_DARK)])
    style.map("Cart.Treeview", background=[("selected", ORANGE_TINT)], foreground=[("selected", TEXT)])
