import customtkinter as ctk
from tkinter import filedialog, messagebox

from src.models.catalog_models import CATEGORY_DEFINITIONS, FEATURE_DEFINITIONS, default_features
from src.services.validation_service import ValidationService
from src.ui.theme import (
    APP_BG,
    CARD_BG,
    GRAPHITE,
    MUTED,
    ON_DARK,
    ON_DARK_MUTED,
    ORANGE,
    ORANGE_DARK,
    SUCCESS_GREEN,
    SURFACE_ALT,
    TEXT,
    button_style,
    font,
)


class FirstRunWizard(ctk.CTkFrame):
    def __init__(self, master, catalog_service, on_complete):
        super().__init__(master, fg_color=APP_BG)
        self.catalog_service = catalog_service
        self.on_complete = on_complete
        self.validation_service = ValidationService()
        self.step = 0

        self.team_name = ctk.StringVar()
        self.model_name = ctk.StringVar()
        self.model_description = ctk.StringVar()
        self.output_folder = ctk.StringVar()
        self.feature_vars = {key: ctk.BooleanVar(value=False) for key, _label in FEATURE_DEFINITIONS}
        self.folder_vars = {category_id: ctk.StringVar() for category_id in CATEGORY_DEFINITIONS}
        self.result_labels = {}

        self.pack(fill="both", expand=True)
        self.render()

    def clear(self):
        for child in self.winfo_children():
            child.destroy()

    def render(self):
        self.clear()
        shell = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10)
        shell.pack(fill="both", expand=True, padx=32, pady=28)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(shell, fg_color=GRAPHITE, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkFrame(header, fg_color=ORANGE, corner_radius=0, height=4).pack(side="bottom", fill="x")
        title = "Bem-vindo ao Montador de Pedido Futebol" if self.step == 0 else "Assistente de Configuração Inicial"
        ctk.CTkLabel(
            header,
            text=title,
            font=font(24, "bold", "italic", brand=True),
            text_color=ON_DARK,
        ).pack(anchor="w", padx=22, pady=(18, 4))
        ctk.CTkLabel(
            header,
            text="Configure o primeiro time, a primeira camisa e as pastas dos arquivos de produção.",
            font=font(14),
            text_color=ON_DARK_MUTED,
        ).pack(anchor="w", padx=22, pady=(0, 18))

        content = ctk.CTkScrollableFrame(shell, fg_color=CARD_BG)
        content.grid(row=1, column=0, sticky="nsew", padx=18, pady=8)
        content.grid_columnconfigure(0, weight=1)

        builders = [
            self.render_welcome,
            self.render_team_step,
            self.render_model_step,
            self.render_features_step,
            self.render_folders_step,
            self.render_naming_step,
            self.render_test_step,
        ]
        builders[self.step](content)

        nav = ctk.CTkFrame(shell, fg_color=CARD_BG)
        nav.grid(row=2, column=0, sticky="ew", padx=18, pady=(8, 18))
        nav.grid_columnconfigure(1, weight=1)
        if self.step > 0:
            ctk.CTkButton(nav, text="Voltar", width=140, command=self.back, **button_style("outline")).grid(
                row=0, column=0, padx=(0, 10)
            )
        ctk.CTkButton(nav, text="Sair", width=120, command=self.master.destroy, **button_style("danger")).grid(
            row=0, column=2, padx=10
        )
        next_text = "Concluir configuração" if self.step == 6 else "Próximo"
        ctk.CTkButton(nav, text=next_text, width=190, command=self.next, **button_style("cta")).grid(
            row=0, column=3
        )

    def render_welcome(self, parent):
        text = (
            "Antes de montar pedidos, precisamos configurar onde estão os arquivos das camisas, "
            "números, letras e logos. O painel principal só será liberado depois que pelo menos "
            "um time e uma camisa estiverem configurados."
        )
        ctk.CTkLabel(parent, text=text, wraplength=900, justify="left", font=ctk.CTkFont(size=17)).grid(
            row=0, column=0, sticky="w", pady=(16, 16)
        )
        ctk.CTkButton(parent, text="Abrir exemplo de como organizar arquivos", command=self.show_example).grid(
            row=1, column=0, sticky="w", pady=8
        )

    def render_team_step(self, parent):
        self.step_title(parent, "1. Criar primeiro time")
        self.entry(parent, "Nome do time", self.team_name, "Exemplo: Brasil, Cruzeiro, Atlético Mineiro")
        self.help(parent, "Digite o nome do time ou coleção que aparecerá no painel.")

    def render_model_step(self, parent):
        self.step_title(parent, "2. Criar primeira camisa")
        self.entry(parent, "Nome da camisa / modelo", self.model_name, "Exemplo: Camisa Branca")
        self.entry(parent, "Observação da camisa", self.model_description, "Exemplo: modelo 2026, números verdes")
        self.help(parent, "Esse nome será usado no painel para o operador selecionar a camisa correta.")

    def render_features_step(self, parent):
        self.step_title(parent, "3. O que essa camisa possui?")
        ctk.CTkLabel(
            parent,
            text="Marque somente o que realmente existe para essa camisa. O painel só mostrará essas opções.",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 14))
        for index, (key, label) in enumerate(FEATURE_DEFINITIONS, start=2):
            ctk.CTkCheckBox(parent, text=label, variable=self.feature_vars[key]).grid(
                row=index, column=0, sticky="w", pady=7
            )

    def render_folders_step(self, parent):
        self.step_title(parent, "4. Selecionar pastas dos arquivos")
        self.folder_row(parent, 1, "Pasta de saída padrão", self.output_folder)
        row = 2
        selected = self.selected_features()
        for category_id, definition in CATEGORY_DEFINITIONS.items():
            if selected.get(definition["feature"]):
                self.folder_row(parent, row, definition["name"], self.folder_vars[category_id])
                row += 1
        if row == 2:
            self.help(parent, "Volte e marque pelo menos um item que essa camisa possui.")

    def render_naming_step(self, parent):
        self.step_title(parent, "5. Como seus arquivos estão nomeados?")
        text = (
            "Letras: A.tif, B.tif, C.tif\n"
            "Números das costas: 0.tif, 1.tif, 2.tif, 10.tif\n"
            "Números da frente: 0 FRENTE.tif, 1 FRENTE.tif, 2 FRENTE.tif\n"
            "Logos e camisa completa: podem ter qualquer nome com extensão .tif ou .tiff\n\n"
            "Evite nomes muito longos ou confusos para letras e números. O sistema identifica letras "
            "e números pelo começo do nome do arquivo."
        )
        ctk.CTkLabel(parent, text=text, justify="left", wraplength=900, font=ctk.CTkFont(size=15)).grid(
            row=1, column=0, sticky="w", pady=8
        )

    def render_test_step(self, parent):
        self.step_title(parent, "6. Testar configuração")
        ctk.CTkLabel(
            parent,
            text="Confira a quantidade de arquivos encontrados nas pastas selecionadas.",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 14))
        self.result_labels = {}
        row = 2
        for category_id, definition in CATEGORY_DEFINITIONS.items():
            if self.selected_features().get(definition["feature"]):
                label = ctk.CTkLabel(parent, text=f"{definition['name']}: aguardando teste", anchor="w")
                label.grid(row=row, column=0, sticky="ew", pady=5)
                self.result_labels[category_id] = label
                row += 1
        ctk.CTkButton(parent, text="Testar novamente", command=self.run_folder_test).grid(
            row=row, column=0, sticky="w", pady=16
        )
        self.after(100, self.run_folder_test)

    def step_title(self, parent, text):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=GRAPHITE,
        ).grid(row=0, column=0, sticky="w", pady=(14, 14))

    def entry(self, parent, label, variable, placeholder):
        row = len(parent.grid_slaves()) + 1
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, sticky="w")
        field = ctk.CTkEntry(parent, textvariable=variable, placeholder_text=placeholder, height=38)
        field.grid(row=row + 1, column=0, sticky="ew", pady=(5, 14))

    def folder_row(self, parent, row, label, variable):
        frame = ctk.CTkFrame(parent, fg_color=SURFACE_ALT)
        frame.grid(row=row, column=0, sticky="ew", pady=6)
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=12, pady=10)
        ctk.CTkEntry(frame, textvariable=variable).grid(row=0, column=1, sticky="ew", padx=8, pady=10)
        ctk.CTkButton(frame, text="Selecionar Pasta", width=150, command=lambda: self.select_folder(variable)).grid(
            row=0, column=2, padx=12, pady=10
        )

    def help(self, parent, text):
        row = len(parent.grid_slaves()) + 1
        ctk.CTkLabel(parent, text=text, text_color=MUTED, anchor="w", wraplength=900).grid(
            row=row, column=0, sticky="ew", pady=8
        )

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

    def show_example(self):
        messagebox.showinfo(
            "Exemplo de organização",
            "GALO 2026 / CAMISA BRANCA\n"
            "  Letras\n"
            "  Números Costas\n"
            "  Números Frente\n"
            "  Logos\n"
            "  Camisa Completa",
            parent=self,
        )

    def run_folder_test(self):
        for category_id, label in self.result_labels.items():
            definition = CATEGORY_DEFINITIONS[category_id]
            category = {
                **definition,
                "id": category_id,
                "folder_path": self.folder_vars[category_id].get(),
                "enabled": True,
            }
            ok, message, count = self.validation_service.validate_folder(category)
            color = SUCCESS_GREEN if ok else ORANGE_DARK
            label.configure(text=f"{definition['name']}: {count} arquivos encontrados ({message})", text_color=color)

    def validate_current_step(self):
        if self.step == 1 and not self.team_name.get().strip():
            messagebox.showwarning("Campo obrigatório", "Informe o nome do time.", parent=self)
            return False
        if self.step == 2 and not self.model_name.get().strip():
            messagebox.showwarning("Campo obrigatório", "Informe o nome da camisa/modelo.", parent=self)
            return False
        if self.step == 3 and not any(self.selected_features().values()):
            messagebox.showwarning("Selecione uma opção", "Marque pelo menos um item que essa camisa possui.", parent=self)
            return False
        if self.step == 4:
            if not self.output_folder.get().strip():
                messagebox.showwarning("Pasta de saída", "Selecione a pasta de saída padrão.", parent=self)
                return False
            missing = [
                CATEGORY_DEFINITIONS[category_id]["name"]
                for category_id, path in self.selected_folder_paths().items()
                if not path.strip()
            ]
            if missing:
                messagebox.showwarning(
                    "Pastas obrigatórias",
                    "Selecione as pastas para:\n" + "\n".join(missing),
                    parent=self,
                )
                return False
        return True

    def next(self):
        if not self.validate_current_step():
            return
        if self.step < 6:
            self.step += 1
            self.render()
            return
        self.finish()

    def back(self):
        self.step = max(0, self.step - 1)
        self.render()

    def finish(self):
        self.catalog_service.create_initial_catalog(
            self.team_name.get(),
            self.model_name.get(),
            self.model_description.get(),
            {**default_features(), **self.selected_features()},
            self.selected_folder_paths(),
            self.output_folder.get(),
        )
        messagebox.showinfo("Configuração concluída", "O painel de produção será aberto agora.", parent=self)
        self.on_complete()
