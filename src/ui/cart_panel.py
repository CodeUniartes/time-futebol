import customtkinter as ctk
from tkinter import ttk

from src.ui.theme import CARD_BG, CARD_BORDER, ORANGE_DARK, SURFACE_ALT, TEXT, apply_table_style, button_style, font


class CartPanel(ctk.CTkFrame):
    def __init__(self, master, cart_service, on_edit, on_remove):
        super().__init__(master, fg_color=CARD_BG, corner_radius=8, border_width=1, border_color=CARD_BORDER)
        self.cart_service = cart_service
        self.on_edit = on_edit
        self.on_remove = on_remove
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(self, fg_color=CARD_BG)
        head.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 8))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            head,
            text="CARRINHO DO PEDIDO",
            font=font(18, "bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w")
        self.badge = ctk.CTkLabel(
            head,
            text="0 itens",
            fg_color=ORANGE_DARK,
            text_color="white",
            corner_radius=13,
            padx=12,
            pady=3,
            font=font(12, "bold"),
        )
        self.badge.grid(row=0, column=1, sticky="e")

        table_frame = ctk.CTkFrame(self, fg_color=CARD_BG, border_width=1, border_color=CARD_BORDER, corner_radius=8)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        apply_table_style(style)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("idx", "source", "category", "item", "quantity", "actions"),
            show="headings",
            selectmode="browse",
            style="Cart.Treeview",
        )
        self.tree.heading("idx", text="#")
        self.tree.heading("source", text="Time / Camisa")
        self.tree.heading("category", text="Categoria")
        self.tree.heading("item", text="Item")
        self.tree.heading("quantity", text="Quantidade")
        self.tree.heading("actions", text="Ações")
        self.tree.column("idx", width=42, anchor="center", stretch=False)
        self.tree.column("source", width=190)
        self.tree.column("category", width=115)
        self.tree.column("item", width=80)
        self.tree.column("quantity", width=98, anchor="center", stretch=False)
        self.tree.column("actions", width=130, anchor="center", stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.tag_configure("odd", background=CARD_BG)
        self.tree.tag_configure("even", background=SURFACE_ALT)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        footer = ctk.CTkFrame(self, fg_color=SURFACE_ALT, corner_radius=8)
        footer.grid(row=2, column=0, sticky="ew", padx=12, pady=(6, 12))
        footer.grid_columnconfigure(1, weight=1)
        self.total_label = ctk.CTkLabel(
            footer,
            text="Total de itens: 0\nTotal de quantidades: 0",
            justify="left",
            text_color=TEXT,
            font=font(14, "bold"),
        )
        self.total_label.grid(row=0, column=0, sticky="w", padx=14, pady=12)
        ctk.CTkButton(
            footer,
            text="Editar quantidade",
            height=38,
            command=self.on_edit,
            **button_style("warning"),
        ).grid(row=0, column=2, padx=8, pady=12)
        ctk.CTkButton(
            footer,
            text="Remover item",
            height=38,
            command=self.on_remove,
            **button_style("danger"),
        ).grid(row=0, column=3, padx=(8, 12), pady=12)
        self.refresh()

    def selected_index(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return int(self.tree.item(selection[0], "values")[0]) - 1

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for index, item in enumerate(self.cart_service.items, start=1):
            tag = "even" if index % 2 == 0 else "odd"
            self.tree.insert(
                "",
                "end",
                values=(index, item.source_label, item.category_name, item.item_label, item.quantity, "Editar | Remover"),
                tags=(tag,),
            )
        total_items = self.cart_service.total_items()
        self.badge.configure(text=f"{total_items} itens")
        self.total_label.configure(
            text=(
                f"Total de itens: {total_items}\n"
                f"Total de quantidades: {self.cart_service.total_quantities()}"
            )
        )
