from pathlib import Path
import sys


if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).resolve().parent
else:
    APP_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = APP_ROOT / "config"
DATA_DIR = APP_ROOT / "data"
SAVED_ORDERS_DIR = DATA_DIR / "pedidos_salvos"
LOGS_DIR = APP_ROOT / "logs"


def app_path(*parts):
    return APP_ROOT.joinpath(*parts)


def ensure_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def existing_folder_or_empty(value):
    if not value:
        return ""
    path = Path(value)
    return str(path) if path.exists() and path.is_dir() else ""
