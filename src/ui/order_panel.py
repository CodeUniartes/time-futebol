import os
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

from src.models.catalog_models import ALL_FILES_LABEL
from src.services.cart_service import CartService
from src.services.file_service import FileService
from src.services.order_service import OrderService
from src.services.settings_service import SettingsService
from src.services.validation_service import ValidationService
from src.ui.cart_panel import CartPanel
from src.ui.saved_orders_window import SavedOrdersWindow
from src.ui.theme import (
    APP_BG,
    CARD_BG,
    CARD_BORDER,
    LIGHT_BLUE,
    LIGHT_GREEN,
    LIGHT_YELLOW,
    MUTED,
    TEXT,
    WARNING_YELLOW,
    button_style,
)
from src.utils.file_name_utils import list_available_items
from src.utils.text_utils import parse_comma_items


ENTRY_STYLE = {
    "height": 34,
    "fg_color": "#ffffff",
    "border_color": "#cfd8e3",
    "border_width": 1,
    "corner_radius": 5,
    "text_color": TEXT,
}

MENU_STYLE = {
    "height": 34,
    "fg_color": "#ffffff",
    "button_color": "#f8fafc",
    "button_hover_color": "#e5eef8",
    "dropdown_fg_color": "#ffffff",
    "dropdown_hover_color": "#e5eef8",
    "text_color": TEXT,
    "corner_radius": 5,
}


class OrderPanel(ctk.CTkFrame):
    def __init__(self, master, catalog_service):
        super().__init__(master, fg_color=APP_BG)
        self.catalog_service = catalog_service
        self.settings_service = SettingsService()
        self.cart_service = CartService()
        self.validation_service = ValidationService()
        self.file_service = FileService()
        self.order_service = OrderService()

        self.catalog = self.catalog_service.load_catalog()
        self.team_map = {}
        self.model_map = {}
        self.category_map = {}
        self.group_category_map = {}
        self.selected_team_id = None
        self.selected_model_id = None
        self.last_validation = None
        self.last_generated_folder = None

        self.client_var = ctk.StringVar()
        self.order_number_var = ctk.StringVar(value=self.settings_service.next_order_number())
        self.note_var = ctk.StringVar()
        self.output_folder_var = ctk.StringVar(value=self.catalog.get("settings", {}).get("default_output_folder", ""))
        self.team_var = ctk.StringVar()
        self.model_var = ctk.StringVar()
        self.model_note_var = ctk.StringVar()
        self.category_var = ctk.StringVar()
        self.item_var = ctk.StringVar()
        self.quantity_var = ctk.StringVar(value="1")
        self.group_category_var = ctk.StringVar()
        self.group_items_var = ctk.StringVar()
        self.group_quantity_var = ctk.StringVar(value="1")

        self.build()
        self.reload_catalog()

    def build(self):
        self.grid_columnconfigure(0, weight=58, uniform="content")
        self.grid_columnconfigure(1, weight=45, uniform="content")
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(self, fg_color=APP_BG, scrollbar_button_color="#c9d7e8")
        left.grid(row=0, column=0, sticky="nsew", padx=(14, 7), pady=14)
        left.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(left, fg_color=APP_BG)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(0, weight=1, uniform="top")
        top.grid_columnconfigure(1, weight=1, uniform="top")
        self.build_order_data(top, 0, 0)
        self.build_selection(top, 0, 1)

        self.build_add_item(left, 1)
        self.build_add_group(left, 2)
        self.build_quick_actions(left, 3)

        bottom = ctk.CTkFrame(left, fg_color=APP_BG)
        bottom.grid(row=4, column=0, sticky="ew", pady=(0, 2))
        bottom.grid_columnconfigure(0, weight=45, uniform="bottom")
        bottom.grid_columnconfigure(1, weight=55, uniform="bottom")
        self.build_validation(bottom, 0, 0)
        self.build_generation(bottom, 0, 1)

        self.cart_panel = CartPanel(self, self.cart_service, self.edit_selected_quantity, self.remove_selected_item)
        self.cart_panel.grid(row=0, column=1, sticky="nsew", padx=(7, 14), pady=14)

    def section(self, parent, row, title, column=0, columnspan=1, fg_color=CARD_BG, padx=0):
        frame = ctk.CTkFrame(
            parent,
            fg_color=fg_color,
            corner_radius=8,
            border_width=1,
            border_color=CARD_BORDER,
        )
        frame.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=padx, pady=(0, 10))
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, columnspan=8, sticky="w", padx=16, pady=(12, 8))
        return frame

    def style_menu(self, menu):
        menu.configure(**MENU_STYLE)
        return menu

    def build_order_data(self, parent, row, column):
        frame = self.section(parent, row, "DADOS DO PEDIDO", column=column, fg_color=CARD_BG, padx=(0, 6))
        frame.grid_columnconfigure(1, weight=1)
        labels = [("Cliente:", self.client_var), ("Pedido nº:", self.order_number_var), ("Observação:", self.note_var)]
        for index, (label, var) in enumerate(labels, start=1):
            ctk.CTkLabel(frame, text=label, text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
                row=index, column=0, sticky="w", padx=(16, 10), pady=5
            )
            ctk.CTkEntry(frame, textvariable=var, **ENTRY_STYLE).grid(
                row=index, column=1, sticky="ew", padx=(0, 16), pady=5
            )
        ctk.CTkLabel(frame, text="Pasta de saída:", text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
            row=4, column=0, sticky="w", padx=(16, 10), pady=(5, 14)
        )
        ctk.CTkEntry(frame, textvariable=self.output_folder_var, **ENTRY_STYLE).grid(
            row=4, column=1, sticky="ew", padx=(0, 8), pady=(5, 14)
        )
        ctk.CTkButton(
            frame,
            text="Selecionar",
            width=96,
            height=34,
            command=self.select_output_folder,
            **button_style("outline"),
        ).grid(row=4, column=2, sticky="e", padx=(0, 16), pady=(5, 14))

    def build_selection(self, parent, row, column):
        frame = self.section(parent, row, "1. SELECIONE TIME E MODELO", column=column, fg_color=CARD_BG, padx=(6, 0))
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="Time:", text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=(16, 10), pady=5
        )
        self.team_menu = self.style_menu(
            ctk.CTkOptionMenu(frame, variable=self.team_var, values=[""], command=self.on_team_change)
        )
        self.team_menu.grid(row=1, column=1, sticky="ew", padx=(0, 16), pady=5)

        ctk.CTkLabel(frame, text="Modelo / Camisa:", text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, sticky="w", padx=(16, 10), pady=5
        )
        self.model_menu = self.style_menu(
            ctk.CTkOptionMenu(frame, variable=self.model_var, values=[""], command=self.on_model_change)
        )
        self.model_menu.grid(row=2, column=1, sticky="ew", padx=(0, 16), pady=5)

        ctk.CTkLabel(
            frame,
            text="Observação do modelo:",
            text_color=TEXT,
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=3, column=0, sticky="w", padx=(16, 10), pady=(5, 14))
        ctk.CTkEntry(frame, textvariable=self.model_note_var, state="disabled", **ENTRY_STYLE).grid(
            row=3, column=1, sticky="ew", padx=(0, 16), pady=(5, 14)
        )

    def build_add_item(self, parent, row):
        frame = self.section(parent, row, "2. ADICIONAR ITEM AO PEDIDO", fg_color=LIGHT_BLUE)
        for index, weight in enumerate([32, 22, 14, 25]):
            frame.grid_columnconfigure(index, weight=weight)
        ctk.CTkLabel(frame, text="Categoria:", text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 4)
        )
        ctk.CTkLabel(frame, text="Item:", text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=1, sticky="w", padx=8, pady=(0, 4)
        )
        ctk.CTkLabel(frame, text="Quantidade:", text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=2, sticky="w", padx=8, pady=(0, 4)
        )
        self.category_menu = self.style_menu(
            ctk.CTkOptionMenu(frame, variable=self.category_var, values=[""], command=self.on_category_change)
        )
        self.category_menu.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.item_menu = self.style_menu(ctk.CTkOptionMenu(frame, variable=self.item_var, values=[""]))
        self.item_menu.grid(row=2, column=1, sticky="ew", padx=8, pady=(0, 16))
        ctk.CTkEntry(frame, textvariable=self.quantity_var, width=88, justify="center", **ENTRY_STYLE).grid(
            row=2, column=2, sticky="ew", padx=8, pady=(0, 16)
        )
        ctk.CTkButton(
            frame,
            text="＋  Adicionar\nao carrinho",
            height=56,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.add_single_item,
            **button_style("primary"),
        ).grid(row=2, column=3, sticky="ew", padx=(14, 16), pady=(0, 16))

    def build_add_group(self, parent, row):
        frame = self.section(parent, row, "3. ADICIONAR GRUPO (VÁRIOS ITENS)", fg_color=LIGHT_GREEN)
        for index, weight in enumerate([30, 30, 16, 25]):
            frame.grid_columnconfigure(index, weight=weight)
        ctk.CTkLabel(frame, text="Categoria:", text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 4)
        )
        ctk.CTkLabel(frame, text="Itens separados por vírgula:", text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=1, sticky="w", padx=8, pady=(0, 4)
        )
        ctk.CTkLabel(frame, text="Quantidade de cada:", text_color=TEXT, font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=2, sticky="w", padx=8, pady=(0, 4)
        )
        self.group_category_menu = self.style_menu(ctk.CTkOptionMenu(frame, variable=self.group_category_var, values=[""]))
        self.group_category_menu.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 6))
        ctk.CTkEntry(
            frame,
            textvariable=self.group_items_var,
            placeholder_text="0, 1, 3",
            **ENTRY_STYLE,
        ).grid(row=2, column=1, sticky="ew", padx=8, pady=(0, 6))
        ctk.CTkEntry(frame, textvariable=self.group_quantity_var, width=92, justify="center", **ENTRY_STYLE).grid(
            row=2, column=2, sticky="ew", padx=8, pady=(0, 6)
        )
        ctk.CTkButton(
            frame,
            text="Adicionar\ngrupo",
            height=56,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.add_group_items,
            **button_style("success"),
        ).grid(row=2, column=3, sticky="ew", padx=(14, 16), pady=(0, 6))
        ctk.CTkLabel(frame, text="Exemplo: 0, 1, 3, 7, 9", text_color="#166534").grid(
            row=3, column=1, columnspan=2, sticky="w", padx=8, pady=(0, 14)
        )

    def build_quick_actions(self, parent, row):
        self.quick_frame = self.section(parent, row, "4. AÇÕES RÁPIDAS", fg_color=LIGHT_YELLOW)
        self.quick_buttons_frame = ctk.CTkFrame(self.quick_frame, fg_color=LIGHT_YELLOW)
        self.quick_buttons_frame.grid(row=1, column=0, columnspan=8, sticky="ew", padx=16, pady=(0, 16))

    def build_validation(self, parent, row, column):
        frame = self.section(parent, row, "5. VALIDAÇÃO", column=column, fg_color=CARD_BG, padx=(0, 6))
        frame.grid_columnconfigure(0, weight=1)
        self.validation_status_frame = ctk.CTkFrame(
            frame,
            fg_color="#f7fff8",
            border_width=1,
            border_color="#73bd80",
            corner_radius=7,
        )
        self.validation_status_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 16))
        self.validation_status_frame.grid_columnconfigure(1, weight=1)
        self.validation_icon = ctk.CTkLabel(
            self.validation_status_frame,
            text="✓",
            width=42,
            height=42,
            fg_color="#2f9e44",
            corner_radius=21,
            text_color="white",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.validation_icon.grid(row=0, column=0, padx=(16, 12), pady=10)
        self.validation_label = ctk.CTkLabel(
            self.validation_status_frame,
            text="Aguardando validação.",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=MUTED,
            anchor="w",
            justify="left",
        )
        self.validation_label.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=10)
        ctk.CTkButton(
            self.validation_status_frame,
            text="Ver detalhes",
            width=110,
            height=34,
            command=self.show_validation_details,
            **button_style("outline"),
        ).grid(row=0, column=2, padx=(8, 16), pady=10)

    def build_generation(self, parent, row, column):
        frame = self.section(parent, row, "6. GERAR PASTA DE PRODUÇÃO", column=column, fg_color=CARD_BG, padx=(6, 0))
        for index in range(4):
            frame.grid_columnconfigure(index, weight=1, uniform="generation")
        ctk.CTkButton(
            frame,
            text="Gerar pasta\nde produção",
            height=58,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.generate_production,
            **button_style("success"),
        ).grid(row=1, column=0, sticky="ew", padx=(16, 8), pady=(0, 16))
        ctk.CTkButton(
            frame,
            text="Abrir pasta\ngerada",
            height=58,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.open_last_generated_folder,
            **button_style("outline"),
        ).grid(row=1, column=1, sticky="ew", padx=8, pady=(0, 16))
        ctk.CTkButton(
            frame,
            text="Resumo do\npedido (TXT)",
            height=58,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.export_summary,
            **button_style("outline"),
        ).grid(row=1, column=2, sticky="ew", padx=8, pady=(0, 16))
        ctk.CTkButton(
            frame,
            text="Limpar\ncarrinho",
            height=58,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.clear_cart,
            **button_style("danger"),
        ).grid(row=1, column=3, sticky="ew", padx=(8, 16), pady=(0, 16))

    def reload_catalog(self):
        self.catalog = self.catalog_service.load_catalog()
        self.output_folder_var.set(self.catalog.get("settings", {}).get("default_output_folder", ""))
        teams = self.catalog.get("teams", [])
        self.team_map = {team["name"]: team["id"] for team in teams}
        team_names = list(self.team_map) or ["Nenhum time configurado"]
        self.team_menu.configure(values=team_names)
        self.team_var.set(team_names[0])
        self.on_team_change(team_names[0])

    def on_team_change(self, selected_name):
        self.selected_team_id = self.team_map.get(selected_name)
        team = self.get_selected_team()
        models = team.get("models", []) if team else []
        self.model_map = {model["name"]: model["id"] for model in models}
        model_names = list(self.model_map) or ["Nenhuma camisa configurada"]
        self.model_menu.configure(values=model_names)
        self.model_var.set(model_names[0])
        self.on_model_change(model_names[0])

    def on_model_change(self, selected_name):
        self.selected_model_id = self.model_map.get(selected_name)
        model = self.get_selected_model()
        description = model.get("description", "") if model else ""
        self.model_note_var.set(description)
        self.update_category_options()
        self.update_quick_actions()
        self.validate_order(silent=True)

    def get_selected_team(self):
        for team in self.catalog.get("teams", []):
            if team.get("id") == self.selected_team_id:
                return team
        return None

    def get_selected_model(self):
        team = self.get_selected_team()
        if not team:
            return None
        for model in team.get("models", []):
            if model.get("id") == self.selected_model_id:
                return model
        return None

    def active_categories(self):
        model = self.get_selected_model()
        if not model:
            return []
        return [category for category in model.get("categories", []) if category.get("enabled")]

    def update_category_options(self):
        categories = self.active_categories()
        self.category_map = {category["name"]: category["id"] for category in categories}
        category_names = list(self.category_map) or ["Nenhuma categoria"]
        self.category_menu.configure(values=category_names)
        self.category_var.set(category_names[0])
        self.on_category_change(category_names[0])

        group_categories = [category for category in categories if self.category_allows_group(category)]
        self.group_category_map = {category["name"]: category["id"] for category in group_categories}
        group_names = list(self.group_category_map) or ["Nenhuma categoria"]
        self.group_category_menu.configure(values=group_names)
        self.group_category_var.set(group_names[0])

    def on_category_change(self, selected_name):
        category = self.category_by_name(selected_name)
        if not category:
            self.item_menu.configure(values=[""])
            self.item_var.set("")
            return
        if self.category_has_selectable_items(category):
            values = list_available_items(category)
            if category.get("quick_action_all_files"):
                values = [ALL_FILES_LABEL] + values
            values = values or [""]
        else:
            values = [ALL_FILES_LABEL]
        self.item_menu.configure(values=values)
        self.item_var.set(values[0])

    def category_by_name(self, selected_name):
        category_id = self.category_map.get(selected_name)
        for category in self.active_categories():
            if category.get("id") == category_id:
                return category
        return None

    def group_category_by_name(self, selected_name):
        category_id = self.group_category_map.get(selected_name)
        for category in self.active_categories():
            if category.get("id") == category_id:
                return category
        return None

    def category_has_selectable_items(self, category):
        return category.get("type") == "individual_from_folder"

    def category_allows_group(self, category):
        return bool(category.get("allow_group_add") and self.category_has_selectable_items(category))

    def update_quick_actions(self):
        for child in self.quick_buttons_frame.winfo_children():
            child.destroy()
        quick_categories = [category for category in self.active_categories() if category.get("quick_action")]
        if not quick_categories:
            ctk.CTkLabel(
                self.quick_buttons_frame,
                text="Nenhuma ação rápida configurada para esta camisa.",
                text_color=MUTED,
            ).grid(row=0, column=0, sticky="w", pady=10)
            return
        icon_map = {
            "camisa_completa": "Camisa\nCompleta",
            "fila_completa_letras": "A-Z\nFila Completa\nde Letras",
            "logos": "Logo\nPatrocinadores",
            "numero_frente": "123\nNúmero Frente",
        }
        for index, category in enumerate(quick_categories):
            self.quick_buttons_frame.grid_columnconfigure(index, weight=1)
            ctk.CTkButton(
                self.quick_buttons_frame,
                text=icon_map.get(category["id"], category["name"]),
                height=58,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda cat=category: self.add_quick_action(cat),
                **button_style("quick"),
            ).grid(row=0, column=index, sticky="ew", padx=6, pady=4)

    def select_output_folder(self):
        path = filedialog.askdirectory(parent=self)
        if path:
            self.output_folder_var.set(path)
            self.catalog_service.update_settings({"default_output_folder": path})

    def get_quantity(self, variable):
        try:
            quantity = int(variable.get())
        except ValueError as exc:
            raise ValueError("A quantidade precisa ser um número inteiro.") from exc
        if quantity <= 0:
            raise ValueError("A quantidade precisa ser maior que zero.")
        return quantity

    def add_single_item(self):
        team = self.get_selected_team()
        model = self.get_selected_model()
        category = self.category_by_name(self.category_var.get())
        if not category:
            messagebox.showwarning("Categoria", "Selecione uma categoria válida.", parent=self)
            return
        item_label = self.item_var.get() if self.category_has_selectable_items(category) else ALL_FILES_LABEL
        try:
            self.cart_service.add_item(team, model, category, item_label, self.get_quantity(self.quantity_var))
        except ValueError as exc:
            messagebox.showwarning("Item inválido", str(exc), parent=self)
            return
        self.cart_panel.refresh()
        self.validate_order(silent=True)

    def add_group_items(self):
        team = self.get_selected_team()
        model = self.get_selected_model()
        category = self.group_category_by_name(self.group_category_var.get())
        if not category:
            messagebox.showwarning("Categoria", "Selecione uma categoria válida para grupo.", parent=self)
            return
        items = parse_comma_items(self.group_items_var.get())
        if not items:
            messagebox.showwarning("Itens", "Informe os itens separados por vírgula.", parent=self)
            return
        try:
            quantity = self.get_quantity(self.group_quantity_var)
            for item_label in items:
                self.cart_service.add_item(team, model, category, item_label, quantity)
        except ValueError as exc:
            messagebox.showwarning("Grupo inválido", str(exc), parent=self)
            return
        self.group_items_var.set("")
        self.cart_panel.refresh()
        self.validate_order(silent=True)

    def add_quick_action(self, category):
        team = self.get_selected_team()
        model = self.get_selected_model()
        dialog = ctk.CTkInputDialog(text=f"Quantidade para {category['name']}:", title="Ação rápida")
        value = dialog.get_input()
        if not value:
            return
        try:
            quantity = int(value)
            self.cart_service.add_item(team, model, category, ALL_FILES_LABEL, quantity)
        except ValueError as exc:
            messagebox.showwarning("Quantidade inválida", str(exc), parent=self)
            return
        self.cart_panel.refresh()
        self.validate_order(silent=True)

    def edit_selected_quantity(self):
        index = self.cart_panel.selected_index()
        if index is None:
            messagebox.showwarning("Selecione", "Selecione um item no carrinho.", parent=self)
            return
        item = self.cart_service.items[index]
        dialog = ctk.CTkInputDialog(text=f"Nova quantidade para {item.item_label}:", title="Editar quantidade")
        value = dialog.get_input()
        if not value:
            return
        try:
            self.cart_service.set_quantity(index, int(value))
        except ValueError as exc:
            messagebox.showwarning("Quantidade inválida", str(exc), parent=self)
            return
        self.cart_panel.refresh()
        self.validate_order(silent=True)

    def remove_selected_item(self):
        index = self.cart_panel.selected_index()
        if index is None:
            messagebox.showwarning("Selecione", "Selecione um item no carrinho.", parent=self)
            return
        self.cart_service.remove(index)
        self.cart_panel.refresh()
        self.validate_order(silent=True)

    def clear_cart(self):
        if not self.cart_service.items:
            return
        if not messagebox.askyesno("Limpar carrinho", "Remover todos os itens do carrinho?", parent=self):
            return
        self.cart_service.clear()
        self.cart_panel.refresh()
        self.validate_order(silent=True)

    def order_info(self):
        return {
            "cliente": self.client_var.get().strip(),
            "numero_pedido": self.order_number_var.get().strip(),
            "observacao": self.note_var.get().strip(),
        }

    def validate_order(self, silent=False):
        team = self.get_selected_team()
        model = self.get_selected_model()
        result = self.validation_service.validate_order(
            self.output_folder_var.get().strip(),
            self.catalog,
            self.cart_service.items,
            fallback_team=team,
            fallback_model=model,
        )
        self.last_validation = result
        if result.ok:
            self.validation_status_frame.configure(fg_color="#f7fff8", border_color="#73bd80")
            self.validation_icon.configure(text="✓", fg_color="#2f9e44")
            self.validation_label.configure(
                text="Tudo pronto!\nTodos os arquivos necessários foram encontrados.",
                text_color="#15803d",
            )
        else:
            first_error = result.errors[0] if result.errors else "Verifique os dados do pedido."
            self.validation_status_frame.configure(fg_color="#fffaf0", border_color="#f0b94d")
            self.validation_icon.configure(text="!", fg_color=WARNING_YELLOW)
            self.validation_label.configure(text=f"Atenção:\n{first_error}", text_color="#b45309")
            if not silent:
                self.show_validation_details()
        return result

    def show_validation_details(self):
        result = self.last_validation or self.validate_order(silent=True)
        lines = []
        if result.errors:
            lines.append("Erros:")
            lines.extend(f"- {error}" for error in result.errors)
        if result.warnings:
            lines.append("\nAvisos:")
            lines.extend(f"- {warning}" for warning in result.warnings)
        if result.found_files:
            lines.append("\nArquivos encontrados por categoria:")
            for category_id, count in result.found_files.items():
                lines.append(f"- {category_id}: {count}")
        if not lines:
            lines.append("Tudo pronto.")
        messagebox.showinfo("Detalhes da validação", "\n".join(lines), parent=self)

    def generate_production(self):
        result = self.validate_order(silent=True)
        if not result.ok:
            self.show_validation_details()
            return
        model = self.get_selected_model()
        try:
            folder, copied, missing = self.file_service.generate(
                self.output_folder_var.get().strip(),
                self.order_info(),
                self.catalog,
                model,
                self.cart_service.items,
                self.catalog.get("settings", {}),
                result,
            )
        except OSError as exc:
            messagebox.showerror("Erro ao gerar", str(exc), parent=self)
            return
        self.last_generated_folder = folder
        message = f"Pasta gerada:\n{folder}\n\nArquivos copiados: {len(copied)}"
        if missing:
            message += "\n\nArquivos faltando:\n" + "\n".join(missing)
        messagebox.showinfo("Produção gerada", message, parent=self)

    def open_last_generated_folder(self):
        if not self.last_generated_folder:
            messagebox.showinfo("Abrir pasta", "Nenhuma pasta foi gerada ainda.", parent=self)
            return
        try:
            os.startfile(self.last_generated_folder)
        except OSError as exc:
            messagebox.showerror("Erro ao abrir", str(exc), parent=self)

    def export_summary(self):
        team = self.get_selected_team()
        model = self.get_selected_model()
        if not team or not model:
            messagebox.showwarning("Seleção", "Selecione time e camisa.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Salvar resumo do pedido",
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt")],
            initialfile=f"resumo_{self.order_number_var.get() or 'pedido'}.txt",
        )
        if not path:
            return
        self.file_service.write_summary(Path(path), self.order_info(), self.catalog, model, self.cart_service.items, [], [])
        messagebox.showinfo("Resumo salvo", f"Resumo salvo em:\n{path}", parent=self)

    def new_order(self):
        if self.cart_service.items and not messagebox.askyesno(
            "Novo pedido", "Limpar o pedido atual e começar um novo?", parent=self
        ):
            return
        self.client_var.set("")
        self.note_var.set("")
        self.order_number_var.set(self.settings_service.next_order_number())
        self.cart_service.clear()
        self.cart_panel.refresh()
        self.validate_order(silent=True)

    def save_order(self):
        path = self.order_service.save_order(
            self.order_info(),
            self.selected_team_id,
            self.selected_model_id,
            self.cart_service.items,
        )
        messagebox.showinfo("Pedido salvo", f"Pedido salvo em:\n{path}", parent=self)

    def open_saved_orders(self):
        SavedOrdersWindow(self, self.order_service, self.load_order_payload)

    def load_order_payload(self, payload):
        order = payload.get("order", {})
        self.client_var.set(order.get("cliente", ""))
        self.order_number_var.set(order.get("numero_pedido", ""))
        self.note_var.set(order.get("observacao", ""))
        self.selected_team_id = payload.get("selected_team_id")
        self.selected_model_id = payload.get("selected_model_id")

        team_name = next(
            (name for name, team_id in self.team_map.items() if team_id == self.selected_team_id),
            None,
        )
        if team_name:
            self.team_var.set(team_name)
            self.on_team_change(team_name)
        model_name = next(
            (name for name, model_id in self.model_map.items() if model_id == self.selected_model_id),
            None,
        )
        if model_name:
            self.model_var.set(model_name)
            self.on_model_change(model_name)
        self.cart_service.load_list(payload.get("items", []))
        self.cart_panel.refresh()
        self.validate_order(silent=True)
