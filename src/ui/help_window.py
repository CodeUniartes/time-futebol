import customtkinter as ctk

from src.ui.assets import apply_app_icon, maximize_window


HELP_TEXT = """
Como preparar as pastas

1. Crie uma pasta para cada camisa
Exemplo: GALO 2026 / CAMISA BRANCA

2. Separe os tipos de arquivo em pastas
Letras
Números Costas
Números Frente
Logos
Camisa Completa

3. Nomeie as letras de forma simples
A.tif
B.tif
C.tif

4. Nomeie os números das costas de forma simples
0.tif
1.tif
2.tif
10.tif

5. Nomeie os números da frente com a palavra FRENTE
0 FRENTE.tif
1 FRENTE.tif
2 FRENTE.tif

6. Logos e camisa completa podem ter qualquer nome
patrocinador_master.tif
logo_manga.tif
camisa_frente.tif

O aplicativo copia os arquivos para a pasta final. Ele nunca apaga nem move os arquivos originais.
"""


class HelpWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Ajuda - Como preparar as pastas")
        self.geometry("760x560")
        apply_app_icon(self)
        maximize_window(self)
        self.grab_set()

        frame = ctk.CTkFrame(self, fg_color="white")
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        label = ctk.CTkLabel(
            frame,
            text="Como preparar as pastas",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#0b3970",
        )
        label.pack(anchor="w", padx=18, pady=(18, 8))

        box = ctk.CTkTextbox(frame, wrap="word", font=ctk.CTkFont(size=15), text_color="#111827")
        box.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        box.insert("1.0", HELP_TEXT.strip())
        box.configure(state="disabled")
