import json
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

from src.models.catalog_models import (
    CATEGORY_DEFINITIONS,
    FEATURE_DEFINITIONS,
    default_features,
    model_menu_map,
    parse_season,
)
from src.services.backup_service import BackupService
from src.services.validation_service import ValidationService
from src.ui.assets import apply_app_icon, maximize_window
from src.ui.help_window import HelpWindow
from src.ui.publish_window import PublishWindow
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
    SURFACE_ALT,
    TEXT,
    button_style,
    font,
)


class ConfigWindow(ctk.CTkToplevel):
    def __init__(self, master, catalog_service, on_saved):
        super().__init__(master)
        self.catalog_service = catalog_service
        self.on_saved = on_saved
        self.backup_service = BackupService(self.catalog_service.catalog_path)
        self.validation_service = ValidationService()
        self.catalog = self.catalog_service.load_catalog()
        self.team_map = {}
        self.model_map = {}
        self.selected_team_id = None
        self.selected_model_id = None

        self.team_var = ctk.StringVar()
        self.model_var = ctk.StringVar()
        self.model_name_var = ctk.StringVar()
        self.model_description_var = ctk.StringVar()
        self.model_season_var = ctk.StringVar()
        self.model_active_var = ctk.BooleanVar(value=True)
        self.output_folder_var = ctk.StringVar(value=self.catalog.get("settings", {}).get("default_output_folder", ""))
        self.feature_vars = {key: ctk.BooleanVar(value=False) for key, _label in FEATURE_DEFINITIONS}
        self.folder_vars = {category_id: ctk.StringVar() for category_id in CATEGORY_DEFINITIONS}

        self.title("Configurações")
        self.geometry("980x690")
        apply_app_icon(self)
        maximize_window(self)
        self.grab_set()
        self.build()
        self.refresh_selectors()

    def build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=GRAPHITE, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkFrame(header, fg_color=ORANGE, corner_radius=0, height=4).pack(side="bottom", fill="x")
        ctk.CTkLabel(
            header,
            text="Configurações",
            font=font(24, "bold", "italic", brand=True),
            text_color=ON_DARK,
        ).pack(anchor="w", padx=22, pady=(16, 2))
        ctk.CTkLabel(
            header,
            text="Cadastre times, camisas e pastas sem editar código.",
            text_color=ON_DARK_MUTED,
        ).pack(anchor="w", padx=22, pady=(0, 16))

        body = ctk.CTkFrame(self, fg_color=APP_BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(body, fg_color=CARD_BG, width=280, corner_radius=10, border_width=1, border_color=CARD_BORDER)
        sidebar.grid(row=0, column=0, sticky="ns", padx=(14, 8), pady=14)
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sidebar, text="Time", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(16, 4)
        )
        self.team_menu = ctk.CTkOptionMenu(sidebar, variable=self.team_var, values=[""], command=self.on_team_change)
        self.team_menu.grid(row=1, column=0, sticky="ew", padx=14, pady=4)
        ctk.CTkButton(sidebar, text="+ Novo Time", command=self.add_team, **button_style("outline")).grid(
            row=2, column=0, sticky="ew", padx=14, pady=(4, 16)
        )

        ctk.CTkLabel(sidebar, text="Camisa / Modelo", font=ctk.CTkFont(weight="bold")).grid(
            row=3, column=0, sticky="w", padx=14, pady=(0, 4)
        )
        self.model_menu = ctk.CTkOptionMenu(sidebar, variable=self.model_var, values=[""], command=self.on_model_change)
        self.model_menu.grid(row=4, column=0, sticky="ew", padx=14, pady=4)
        ctk.CTkButton(sidebar, text="+ Nova Camisa", command=self.add_model, **button_style("outline")).grid(
            row=5, column=0, sticky="ew", padx=14, pady=(4, 16)
        )

        ctk.CTkButton(sidebar, text="Ajuda", command=lambda: HelpWindow(self), **button_style("muted")).grid(
            row=6, column=0, sticky="ew", padx=14, pady=4
        )
        ctk.CTkButton(sidebar, text="Fazer backup", command=self.create_backup, **button_style("muted")).grid(
            row=7, column=0, sticky="ew", padx=14, pady=4
        )
        ctk.CTkButton(sidebar, text="Restaurar backup", command=self.restore_backup, **button_style("muted")).grid(
            row=8, column=0, sticky="ew", padx=14, pady=4
        )
        ctk.CTkButton(sidebar, text="Editar JSON avançado", command=self.open_advanced_json, **button_style("warning")).grid(
            row=9, column=0, sticky="ew", padx=14, pady=4
        )

        self.form = ctk.CTkScrollableFrame(body, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER)
        self.form.grid(row=0, column=1, sticky="nsew", padx=(8, 14), pady=14)
        self.form.grid_columnconfigure(1, weight=1)
        self.build_form()

    def build_form(self):
        for child in self.form.winfo_children():
            child.destroy()

        ctk.CTkLabel(
            self.form,
            text="Dados da camisa",
            font=font(20, "bold"),
            text_color=GRAPHITE,
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(16, 10))

        self.label_entry(self.form, 1, "Nome da camisa / modelo", self.model_name_var)
        self.label_entry(self.form, 2, "Observação", self.model_description_var)
        self.label_entry(self.form, 3, "Ano (opcional, ex.: 2026)", self.model_season_var)
        ctk.CTkCheckBox(self.form, text="Ativa (aparece no site)", variable=self.model_active_var).grid(
            row=4, column=0, columnspan=3, sticky="w", padx=14, pady=7
        )
        self.folder_picker(self.form, 5, "Pasta de saída padrão", self.output_folder_var)

        ctk.CTkLabel(
            self.form,
            text="O que essa camisa possui?",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=6, column=0, columnspan=3, sticky="w", padx=14, pady=(18, 8))

        row = 7
        for key, label in FEATURE_DEFINITIONS:
            ctk.CTkCheckBox(self.form, text=label, variable=self.feature_vars[key], command=self.build_folder_rows).grid(
                row=row, column=0, columnspan=3, sticky="w", padx=14, pady=5
            )
            row += 1

        self.folder_frame = ctk.CTkFrame(self.form, fg_color=SURFACE_ALT)
        self.folder_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=14, pady=(18, 12))
        self.folder_frame.grid_columnconfigure(1, weight=1)
        self.build_folder_rows()

        actions = ctk.CTkFrame(self.form, fg_color=CARD_BG)
        actions.grid(row=row + 1, column=0, columnspan=3, sticky="ew", padx=14, pady=16)
        actions.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(actions, text="Testar pastas", command=self.test_folders, **button_style("outline")).grid(
            row=0, column=1, padx=8
        )
        ctk.CTkButton(actions, text="Publicar Catálogo", command=self.open_publish, **button_style("primary")).grid(
            row=0, column=2, padx=8
        )
        ctk.CTkButton(actions, text="Salvar Configuração", command=self.save, **button_style("cta")).grid(
            row=0, column=3, padx=8
        )

    def label_entry(self, parent, row, label, variable):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=14, pady=7
        )
        ctk.CTkEntry(parent, textvariable=variable).grid(row=row, column=1, columnspan=2, sticky="ew", padx=14, pady=7)

    def folder_picker(self, parent, row, label, variable):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=14, pady=7
        )
        ctk.CTkEntry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=14, pady=7)
        ctk.CTkButton(parent, text="Selecionar Pasta", width=150, command=lambda: self.select_folder(variable)).grid(
            row=row, column=2, sticky="e", padx=14, pady=7
        )

    def build_folder_rows(self):
        if not hasattr(self, "folder_frame"):
            return
        for child in self.folder_frame.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self.folder_frame,
            text="Pastas dos arquivos",
            font=font(16, "bold"),
            text_color=GRAPHITE,
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 8))
        row = 1
        selected_count = 0
        for category_id, definition in CATEGORY_DEFINITIONS.items():
            if self.feature_vars[definition["feature"]].get():
                selected_count += 1
                ctk.CTkLabel(self.folder_frame, text=definition["name"]).grid(
                    row=row, column=0, sticky="w", padx=12, pady=6
                )
                ctk.CTkEntry(self.folder_frame, textvariable=self.folder_vars[category_id]).grid(
                    row=row, column=1, sticky="ew", padx=8, pady=6
                )
                ctk.CTkButton(
                    self.folder_frame,
                    text="Selecionar",
                    width=110,
                    command=lambda var=self.folder_vars[category_id]: self.select_folder(var),
                ).grid(row=row, column=2, padx=12, pady=6)
                row += 1
        if not selected_count:
            ctk.CTkLabel(
                self.folder_frame,
                text="Marque acima os itens que essa camisa possui para liberar os campos de pasta.",
                text_color=MUTED,
            ).grid(row=1, column=0, columnspan=3, sticky="w", padx=12, pady=12)

    def refresh_selectors(self):
        self.catalog = self.catalog_service.load_catalog()
        teams = self.catalog.get("teams", [])
        self.team_map = {team["name"]: team["id"] for team in teams}
        team_names = list(self.team_map) or ["Nenhum time cadastrado"]
        self.team_menu.configure(values=team_names)
        if self.selected_team_id:
            selected = next((team["name"] for team in teams if team["id"] == self.selected_team_id), team_names[0])
        else:
            selected = team_names[0]
        self.team_var.set(selected)
        self.on_team_change(selected)

    def on_team_change(self, selected_name):
        self.selected_team_id = self.team_map.get(selected_name)
        team = self.get_selected_team()
        models = team.get("models", []) if team else []
        self.model_map = model_menu_map(models)
        model_names = list(self.model_map) or ["Nenhuma camisa cadastrada"]
        self.model_menu.configure(values=model_names)
        self.model_var.set(model_names[0])
        self.on_model_change(model_names[0])

    def on_model_change(self, selected_name):
        self.selected_model_id = self.model_map.get(selected_name)
        model = self.get_selected_model()
        self.load_model(model)

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

    def load_model(self, model):
        for var in self.folder_vars.values():
            var.set("")
        for key in self.feature_vars:
            self.feature_vars[key].set(False)
        if not model:
            self.model_name_var.set("")
            self.model_description_var.set("")
            self.model_season_var.set("")
            self.model_active_var.set(True)
            self.build_folder_rows()
            return
        self.model_name_var.set(model.get("name", ""))
        self.model_description_var.set(model.get("description", ""))
        self.model_season_var.set(str(model.get("season") or ""))
        self.model_active_var.set(bool(model.get("active", True)))
        features = {**default_features(), **model.get("features", {})}
        for key, value in features.items():
            if key in self.feature_vars:
                self.feature_vars[key].set(bool(value))
        for category in model.get("categories", []):
            if category.get("id") in self.folder_vars:
                self.folder_vars[category["id"]].set(category.get("folder_path", ""))
        self.build_folder_rows()

    def selected_features(self):
        return {key: var.get() for key, var in self.feature_vars.items()}

    def selected_folder_paths(self):
        features = self.selected_features()
        return {
            category_id: var.get()
            for category_id, var in self.folder_vars.items()
            if features.get(CATEGORY_DEFINITIONS[category_id]["feature"])
        }

    def select_folder(self, variable):
        path = filedialog.askdirectory(parent=self)
        if path:
            variable.set(path)

    def add_team(self):
        dialog = ctk.CTkInputDialog(text="Nome do novo time:", title="Novo Time")
        name = dialog.get_input()
        if not name:
            return
        team = self.catalog_service.add_team(name)
        self.selected_team_id = team["id"]
        self.refresh_selectors()

    def add_model(self):
        if not self.selected_team_id:
            messagebox.showwarning("Time obrigatório", "Crie ou selecione um time primeiro.", parent=self)
            return
        dialog = ctk.CTkInputDialog(text="Nome da nova camisa/modelo:", title="Nova Camisa")
        name = dialog.get_input()
        if not name:
            return
        model = self.catalog_service.add_model(self.selected_team_id, name, "", default_features(), {})
        self.selected_model_id = model["id"]
        self.refresh_selectors()

    def save(self):
        if not self.selected_team_id:
            messagebox.showwarning("Time obrigatório", "Crie ou selecione um time.", parent=self)
            return
        if not self.model_name_var.get().strip():
            messagebox.showwarning("Nome obrigatório", "Informe o nome da camisa/modelo.", parent=self)
            return
        if not any(self.selected_features().values()):
            messagebox.showwarning("Selecione uma opção", "Marque pelo menos um item que essa camisa possui.", parent=self)
            return
        try:
            season = parse_season(self.model_season_var.get())
        except ValueError as error:
            messagebox.showwarning("Ano inválido", str(error), parent=self)
            return
        self.catalog_service.update_settings({"default_output_folder": self.output_folder_var.get()})
        if self.selected_model_id:
            model = self.catalog_service.update_model(
                self.selected_team_id,
                self.selected_model_id,
                self.model_name_var.get(),
                self.model_description_var.get(),
                self.selected_features(),
                self.selected_folder_paths(),
                season=season,
                active=self.model_active_var.get(),
            )
        else:
            model = self.catalog_service.add_model(
                self.selected_team_id,
                self.model_name_var.get(),
                self.model_description_var.get(),
                self.selected_features(),
                self.selected_folder_paths(),
                season=season,
                active=self.model_active_var.get(),
            )
        self.selected_model_id = model["id"]
        self.catalog = self.catalog_service.load_catalog()
        self.refresh_selectors()
        self.on_saved()
        messagebox.showinfo("Salvo", "Configuração salva com sucesso.", parent=self)

    def open_publish(self):
        PublishWindow(self, self.catalog_service)

    def test_folders(self):
        messages = []
        for category_id, path in self.selected_folder_paths().items():
            category = {
                **CATEGORY_DEFINITIONS[category_id],
                "id": category_id,
                "folder_path": path,
                "enabled": True,
            }
            ok, message, count = self.validation_service.validate_folder(category)
            status = "OK" if ok else "Atenção"
            messages.append(f"{CATEGORY_DEFINITIONS[category_id]['name']}: {count} arquivos ({status} - {message})")
        if not messages:
            messages.append("Nenhuma categoria marcada.")
        messagebox.showinfo("Teste de pastas", "\n".join(messages), parent=self)

    def create_backup(self):
        path = self.backup_service.create_backup()
        messagebox.showinfo("Backup criado", f"Backup salvo em:\n{path}", parent=self)

    def restore_backup(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Restaurar backup",
            filetypes=[("JSON", "*.json")],
            initialdir=str(Path(self.catalog_service.catalog_path).parent / "backups"),
        )
        if not path:
            return
        self.backup_service.restore_backup(path)
        self.catalog = self.catalog_service.load_catalog()
        self.refresh_selectors()
        self.on_saved()
        messagebox.showinfo("Backup restaurado", "Configuração restaurada com sucesso.", parent=self)

    def open_advanced_json(self):
        window = ctk.CTkToplevel(self)
        window.title("Edição avançada do JSON")
        window.geometry("860x620")
        apply_app_icon(window)
        maximize_window(window)
        window.grab_set()
        frame = ctk.CTkFrame(window, fg_color=CARD_BG)
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            frame,
            text="Uso técnico: editar este JSON incorretamente pode quebrar a configuração.",
            text_color=ORANGE_DARK,
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=10)
        textbox = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=12))
        textbox.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        textbox.insert("1.0", json.dumps(self.catalog_service.load_catalog(), ensure_ascii=False, indent=2))

        def save_advanced():
            try:
                data = json.loads(textbox.get("1.0", "end"))
            except json.JSONDecodeError as exc:
                messagebox.showerror("JSON inválido", str(exc), parent=window)
                return
            self.catalog_service.save_catalog(data)
            self.catalog = self.catalog_service.load_catalog()
            self.refresh_selectors()
            self.on_saved()
            window.destroy()
            messagebox.showinfo("Salvo", "JSON avançado salvo.", parent=self)

        buttons = ctk.CTkFrame(frame, fg_color=CARD_BG)
        buttons.grid(row=2, column=0, sticky="ew", padx=12, pady=10)
        buttons.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(buttons, text="Salvar JSON", command=save_advanced, **button_style("cta")).grid(
            row=0, column=1, padx=8
        )
        ctk.CTkButton(buttons, text="Cancelar", command=window.destroy, **button_style("outline")).grid(
            row=0, column=2
        )
