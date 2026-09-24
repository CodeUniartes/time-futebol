import os
import customtkinter as ctk
from tkinter import messagebox

from src.services.background_publish import BackgroundPublish
from src.services.publish_service import REPORT_FILE, PublishService
from src.services.site_config_service import SiteConfigService
from src.ui.assets import apply_app_icon
from src.ui.theme import GRAPHITE, MUTED, TEXT, button_style, font

POLL_MS = 100


class PublishWindow(ctk.CTkToplevel):
    def __init__(self, master, catalog_service):
        super().__init__(master)
        self.site_config = SiteConfigService()
        self.runner = BackgroundPublish(PublishService(catalog_service, self.site_config))
        self.output_dir = self.site_config.publish_dir()

        self.title("Publicar Catálogo")
        self.geometry("760x450")
        self.minsize(700, 420)
        apply_app_icon(self)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build()

    def build(self):
        frame = ctk.CTkFrame(self, fg_color="white")
        frame.pack(fill="both", expand=True, padx=18, pady=18)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Publicar Catálogo", font=font(22, "bold", "italic", brand=True), text_color=GRAPHITE).grid(
            row=0, column=0, sticky="w", padx=14, pady=(14, 4)
        )
        ctk.CTkLabel(
            frame,
            text=(
                "Gera o catálogo público e as prévias (imagens leves com marca d'água) das camisas ativas. "
                "Os arquivos .tif originais não são alterados nem enviados."
            ),
            wraplength=680,
            justify="left",
            text_color=MUTED,
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))
        ctk.CTkLabel(frame, text=f"Pasta de saída: {self.output_dir}", wraplength=680, justify="left", text_color=MUTED).grid(
            row=2, column=0, sticky="w", padx=14, pady=(0, 12)
        )

        self.progress_bar = ctk.CTkProgressBar(frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 6))
        self.status_label = ctk.CTkLabel(frame, text="Pronto para gerar.", anchor="w", text_color=TEXT)
        self.status_label.grid(row=4, column=0, sticky="ew", padx=14)

        self.summary = ctk.CTkTextbox(frame, height=120, state="disabled")
        self.summary.grid(row=5, column=0, sticky="nsew", padx=14, pady=12)
        frame.grid_rowconfigure(5, weight=1)

        buttons = ctk.CTkFrame(frame, fg_color="white")
        buttons.grid(row=6, column=0, sticky="ew", padx=14, pady=(0, 14))
        buttons.grid_columnconfigure(0, weight=1)
        self.start_button = ctk.CTkButton(buttons, text="Gerar catálogo", command=self.start, **button_style("cta"))
        self.start_button.grid(row=0, column=1, padx=6)
        self.cancel_button = ctk.CTkButton(
            buttons, text="Cancelar", command=self.cancel, state="disabled", **button_style("warning")
        )
        self.cancel_button.grid(row=0, column=2, padx=6)
        self.folder_button = ctk.CTkButton(
            buttons, text="Abrir pasta", command=self.open_folder, state="disabled", **button_style("outline")
        )
        self.folder_button.grid(row=0, column=3, padx=6)
        self.report_button = ctk.CTkButton(
            buttons, text="Ver relatório", command=self.open_report, state="disabled", **button_style("outline")
        )
        self.report_button.grid(row=0, column=4, padx=6)

    def start(self):
        self.progress_bar.set(0)
        self.write_summary("")
        self.status_label.configure(text="Preparando...")
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.runner.start()
        self.after(POLL_MS, self.poll)

    def cancel(self):
        self.runner.cancel()
        self.cancel_button.configure(state="disabled")
        self.status_label.configure(text="Cancelando...")

    def poll(self):
        for event in self.runner.poll():
            kind = event[0]
            if kind == "progress":
                _kind, done, total, name = event
                self.progress_bar.set(done / total if total else 0)
                self.status_label.configure(text=f"{done} de {total}: {name}")
            elif kind == "done":
                self.finish(event[1])
                return
            elif kind == "error":
                self.fail(event[1])
                return
        if self.runner.running or not self.runner.events.empty():
            self.after(POLL_MS, self.poll)

    def finish(self, result):
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        if result.cancelled:
            self.status_label.configure(text="Cancelado. O catálogo anterior foi mantido.")
            return
        self.progress_bar.set(1)
        self.status_label.configure(text="Concluído.")
        self.folder_button.configure(state="normal")
        self.report_button.configure(state="normal")
        lines = [
            f"Itens publicados: {result.item_count}",
            f"Prévias geradas: {result.generated} | reaproveitadas: {result.reused}",
            f"Falhas: {len(result.failures)} | Avisos: {len(result.warnings)}",
        ]
        lines += [f"- Falha: {failure}" for failure in result.failures[:5]]
        lines += [f"- Aviso: {warning}" for warning in result.warnings[:5]]
        if len(result.failures) > 5 or len(result.warnings) > 5:
            lines.append("... veja o relatório completo.")
        self.write_summary("\n".join(lines))

    def fail(self, message):
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.status_label.configure(text="Erro ao gerar o catálogo.")
        messagebox.showerror("Publicar catálogo", f"Não foi possível gerar o catálogo:\n{message}", parent=self)

    def write_summary(self, text):
        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", text)
        self.summary.configure(state="disabled")

    def open_folder(self):
        self.open_path(self.output_dir)

    def open_report(self):
        self.open_path(self.output_dir / REPORT_FILE)

    def open_path(self, path):
        try:
            os.startfile(path)
        except OSError as error:
            messagebox.showwarning("Abrir", f"Não foi possível abrir:\n{path}\n{error}", parent=self)

    def close(self):
        if self.runner.running:
            if not messagebox.askyesno("Publicar catálogo", "A geração está em andamento. Cancelar e fechar?", parent=self):
                return
            self.runner.cancel()
        self.destroy()
