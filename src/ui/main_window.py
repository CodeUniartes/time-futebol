import customtkinter as ctk
import tkinter as tk

from src.services.catalog_service import CatalogService
from src.ui.assets import apply_app_icon, load_photo, maximize_window
from src.ui.config_window import ConfigWindow
from src.ui.first_run_wizard import FirstRunWizard
from src.ui.order_panel import OrderPanel
from src.ui.theme import APP_BG, HEADER_BLUE, HEADER_BLUE_DARK


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

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
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=HEADER_BLUE, corner_radius=0, height=76)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        self.header_logo_image = load_photo("logo_cabecalho.png", max_width=72, max_height=62)
        tk.Label(header, image=self.header_logo_image, bg=HEADER_BLUE, bd=0, highlightthickness=0).grid(
            row=0, column=0, rowspan=2, sticky="w", padx=(18, 8), pady=7
        )

        ctk.CTkLabel(
            header,
            text="MONTADOR DE PEDIDO - FUTEBOL",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white",
        ).grid(row=0, column=1, sticky="w", padx=(8, 12), pady=(14, 0))
        ctk.CTkLabel(
            header,
            text="Painel de Produção",
            font=ctk.CTkFont(size=14),
            text_color="#dbeafe",
        ).grid(row=1, column=1, sticky="w", padx=(8, 12), pady=(0, 12))

        toolbar = ctk.CTkFrame(header, fg_color="#f8fafc", corner_radius=0)
        toolbar.grid(row=0, column=2, rowspan=2, sticky="nse", padx=0, pady=0)
        toolbar.grid_rowconfigure(0, weight=1)
        buttons = [
            ("\ue8a5", "Novo Pedido", self.new_order),
            ("\ue74e", "Salvar", self.save_order),
            ("\ue8b7", "Pedidos Salvos", self.open_saved_orders),
            ("\ue713", "Configurações", self.open_config),
        ]
        for index, (icon, text, command) in enumerate(buttons):
            self.toolbar_button(toolbar, index, icon, text, command)

        self.order_panel = OrderPanel(self, self.catalog_service)
        self.order_panel.grid(row=1, column=0, sticky="nsew")

        footer = ctk.CTkFrame(self, fg_color="#f8fafc", corner_radius=0, height=32)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(footer, text="✓ Pedido salvo automaticamente", text_color="#0b7a35").grid(
            row=0, column=0, sticky="w", padx=22, pady=6
        )
        ctk.CTkLabel(footer, text="Pasta de origem: configure em Dados do Pedido", text_color=HEADER_BLUE_DARK).grid(
            row=0, column=1, sticky="n", padx=22, pady=6
        )
        ctk.CTkLabel(footer, text="Versão 1.0.0", text_color=HEADER_BLUE_DARK).grid(
            row=0, column=2, sticky="e", padx=22, pady=6
        )

    def toolbar_button(self, parent, column, icon, text, command):
        cell = ctk.CTkFrame(parent, fg_color="#f8fafc", corner_radius=0, width=130, height=76)
        cell.grid(row=0, column=column, sticky="nsew")
        cell.grid_propagate(False)
        cell.grid_rowconfigure(0, weight=1)
        cell.grid_rowconfigure(1, weight=1)
        icon_label = ctk.CTkLabel(
            cell,
            text=icon,
            font=ctk.CTkFont(family="Segoe MDL2 Assets", size=25),
            text_color="#111827",
        )
        icon_label.grid(row=0, column=0, pady=(8, 0), padx=20)
        text_label = ctk.CTkLabel(
            cell,
            text=text,
            font=ctk.CTkFont(size=13),
            text_color="#111827",
        )
        text_label.grid(row=1, column=0, pady=(0, 8), padx=20)
        for widget in (cell, icon_label, text_label):
            widget.bind("<Button-1>", lambda _event, callback=command: callback())
            widget.bind("<Enter>", lambda _event, frame=cell: frame.configure(fg_color="#e8f1fb"))
            widget.bind("<Leave>", lambda _event, frame=cell: frame.configure(fg_color="#f8fafc"))

    def new_order(self):
        if self.order_panel:
            self.order_panel.new_order()

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
