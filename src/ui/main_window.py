import customtkinter as ctk
import tkinter as tk

from src.services.catalog_service import CatalogService
from src.ui.assets import apply_app_icon, load_photo, maximize_window
from src.ui.config_window import ConfigWindow
from src.ui.first_run_wizard import FirstRunWizard
from src.ui.order_panel import OrderPanel
from src.ui.theme import (
    APP_BG,
    CARD_BG,
    CARD_BORDER,
    GRAPHITE,
    MUTED,
    ON_DARK,
    ON_DARK_MUTED,
    ORANGE,
    ORANGE_DARK,
    SUCCESS_GREEN,
    apply_brand_theme,
    font,
)


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_brand_theme(self)

        self.catalog_service = CatalogService()
        self.order_panel = None
        self.header_logo_image = None

        self.title("Montador de Pedido - Futebol")
        self.geometry("1360x760")
        self.minsize(1180, 700)
        self.configure(fg_color=APP_BG)
        apply_app_icon(self)
        maximize_window(self)
        self.show_initial_screen()

    def clear(self):
        for child in self.winfo_children():
            child.destroy()

    def show_initial_screen(self):
        self.clear()
        if self.catalog_service.is_configured():
            self.show_main_panel()
        else:
            FirstRunWizard(self, self.catalog_service, self.show_main_panel)

    def show_main_panel(self):
        self.clear()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color=GRAPHITE, corner_radius=0, height=80)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        self.header_logo_image = load_photo("logo_cabecalho.png", max_width=90, max_height=68)
        tk.Label(header, image=self.header_logo_image, bg=GRAPHITE, bd=0, highlightthickness=0).grid(
            row=0, column=0, rowspan=2, sticky="w", padx=(20, 10), pady=7
        )
        ctk.CTkFrame(self, fg_color=ORANGE, corner_radius=0, height=4).grid(row=1, column=0, sticky="ew")

        ctk.CTkLabel(
            header,
            text="MONTADOR DE PEDIDO - FUTEBOL",
            font=font(24, "bold", "italic", brand=True),
            text_color=ON_DARK,
        ).grid(row=0, column=1, sticky="w", padx=(8, 12), pady=(14, 0))
        ctk.CTkLabel(
            header,
            text="Painel de Produção",
            font=font(14),
            text_color=ON_DARK_MUTED,
        ).grid(row=1, column=1, sticky="w", padx=(8, 12), pady=(0, 12))

        toolbar = ctk.CTkFrame(header, fg_color=GRAPHITE, corner_radius=0)
        toolbar.grid(row=0, column=2, rowspan=2, sticky="nse", padx=0, pady=0)
        toolbar.grid_rowconfigure(0, weight=1)
        buttons = [
            ("\ue8a5", "Novo Pedido", self.new_order),
            ("\ue8e5", "Importar Pedido", self.import_order),
            ("\ue74e", "Salvar", self.save_order),
            ("\ue8b7", "Pedidos Salvos", self.open_saved_orders),
            ("\ue713", "Configurações", self.open_config),
        ]
        for index, (icon, text, command) in enumerate(buttons):
            self.toolbar_button(toolbar, index, icon, text, command)

        self.order_panel = OrderPanel(self, self.catalog_service)
        self.order_panel.grid(row=2, column=0, sticky="nsew")

        footer = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0, height=34, border_width=1, border_color=CARD_BORDER)
        footer.grid(row=3, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(footer, text="✓ Pedido salvo automaticamente", text_color=SUCCESS_GREEN).grid(
            row=0, column=0, sticky="w", padx=22, pady=6
        )
        ctk.CTkLabel(footer, text="Pasta de origem: configure em Dados do Pedido", text_color=MUTED).grid(
            row=0, column=1, sticky="n", padx=22, pady=6
        )
        ctk.CTkLabel(footer, text="Uniartes Uniformes · Versão 1.0.0", text_color=MUTED).grid(
            row=0, column=2, sticky="e", padx=22, pady=6
        )

    def toolbar_button(self, parent, column, icon, text, command):
        cell = ctk.CTkFrame(parent, fg_color=GRAPHITE, corner_radius=0, width=116, height=80)
        cell.grid(row=0, column=column, sticky="nsew")
        cell.grid_propagate(False)
        cell.grid_rowconfigure(0, weight=1)
        cell.grid_rowconfigure(1, weight=1)
        icon_label = ctk.CTkLabel(
            cell,
            text=icon,
            font=ctk.CTkFont(family="Segoe MDL2 Assets", size=25),
            text_color=ON_DARK,
        )
        icon_label.grid(row=0, column=0, pady=(8, 0), padx=20)
        text_label = ctk.CTkLabel(
            cell,
            text=text,
            font=font(13),
            text_color=ON_DARK,
        )
        text_label.grid(row=1, column=0, pady=(0, 8), padx=20)
        for widget in (cell, icon_label, text_label):
            widget.bind("<Button-1>", lambda _event, callback=command: callback())
            widget.bind("<Enter>", lambda _event, frame=cell: frame.configure(fg_color=ORANGE_DARK))
            widget.bind("<Leave>", lambda _event, frame=cell: frame.configure(fg_color=GRAPHITE))

    def new_order(self):
        if self.order_panel:
            self.order_panel.new_order()

    def import_order(self):
        if self.order_panel:
            self.order_panel.import_order()

    def save_order(self):
        if self.order_panel:
            self.order_panel.save_order()

    def open_saved_orders(self):
        if self.order_panel:
            self.order_panel.open_saved_orders()

    def open_config(self):
        ConfigWindow(self, self.catalog_service, self.on_config_saved)

    def on_config_saved(self):
        if self.order_panel:
            self.order_panel.reload_catalog()
