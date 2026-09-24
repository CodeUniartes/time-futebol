import customtkinter as ctk
from tkinter import Listbox, messagebox

from src.ui.assets import apply_app_icon, maximize_window
from src.ui.theme import CARD_BG, GRAPHITE, button_style, font


class SavedOrdersWindow(ctk.CTkToplevel):
    def __init__(self, master, order_service, on_load):
        super().__init__(master)
        self.order_service = order_service
        self.on_load = on_load
        self.paths = []
        self.title("Pedidos Salvos")
        self.geometry("720x460")
        apply_app_icon(self)
        maximize_window(self)
        self.grab_set()

        frame = ctk.CTkFrame(self, fg_color=CARD_BG)
        frame.pack(fill="both", expand=True, padx=18, pady=18)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="Pedidos Salvos",
            font=font(22, "bold", "italic", brand=True),
            text_color=GRAPHITE,
        ).grid(row=0, column=0, sticky="w", padx=12, pady=12)

        self.listbox = Listbox(frame, font=("Segoe UI", 11), activestyle="dotbox")
        self.listbox.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)

        buttons = ctk.CTkFrame(frame, fg_color=CARD_BG)
        buttons.grid(row=2, column=0, sticky="ew", padx=12, pady=12)
        buttons.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(buttons, text="Carregar pedido", command=self.load_selected, **button_style("cta")).grid(row=0, column=1, padx=8)
        ctk.CTkButton(buttons, text="Fechar", command=self.destroy, **button_style("outline")).grid(row=0, column=2)
        self.refresh()

    def refresh(self):
        self.paths = self.order_service.list_orders()
        self.listbox.delete(0, "end")
        for path in self.paths:
            self.listbox.insert("end", path.name)

    def load_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Selecione", "Selecione um pedido salvo.", parent=self)
            return
        path = self.paths[selection[0]]
        payload = self.order_service.load_order(path)
        self.on_load(payload)
        self.destroy()
