import math
import sys
from pathlib import Path
import tkinter as tk

from src.utils.path_utils import APP_ROOT


def resource_path(*parts):
    base = Path(getattr(sys, "_MEIPASS", APP_ROOT))
    return base.joinpath(*parts)


def asset_path(filename):
    return resource_path("assets", filename)


def load_photo(filename, max_width=None, max_height=None):
    image = tk.PhotoImage(file=str(asset_path(filename)))
    factor = 1
    if max_width and image.width() > max_width:
        factor = max(factor, math.ceil(image.width() / max_width))
    if max_height and image.height() > max_height:
        factor = max(factor, math.ceil(image.height() / max_height))
    if factor > 1:
        image = image.subsample(factor, factor)
    return image


def apply_app_icon(window):
    try:
        window.iconbitmap(str(asset_path("icon.ico")))
    except Exception:
        pass
    try:
        image = load_photo("icon.png", max_width=128, max_height=128)
        window.iconphoto(True, image)
        window._app_icon_image = image
    except Exception:
        pass


def maximize_window(window):
    def do_maximize():
        try:
            window.state("zoomed")
            return
        except Exception:
            pass
        try:
            width = window.winfo_screenwidth()
            height = window.winfo_screenheight()
            window.geometry(f"{width}x{height}+0+0")
        except Exception:
            pass

    window.after(50, do_maximize)
