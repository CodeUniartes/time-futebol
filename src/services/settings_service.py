from datetime import datetime

from src.utils.json_utils import load_json, save_json
from src.utils.path_utils import CONFIG_DIR


DEFAULT_SETTINGS = {
    "schema_version": 1,
    "last_order_number": "",
    "window_geometry": "1280x760",
}


class SettingsService:
    def __init__(self, settings_path=None):
        self.settings_path = settings_path or CONFIG_DIR / "settings.json"
        if not self.settings_path.exists():
            save_json(self.settings_path, DEFAULT_SETTINGS)

    def load(self):
        data = load_json(self.settings_path, DEFAULT_SETTINGS.copy())
        data = {**DEFAULT_SETTINGS, **(data or {})}
        return data

    def save(self, data):
        save_json(self.settings_path, {**DEFAULT_SETTINGS, **data})

    def next_order_number(self):
        data = self.load()
        prefix = datetime.now().strftime("%d%m%Y")
        last = str(data.get("last_order_number") or "")
        counter = 1
        if last.startswith(prefix + "_"):
            try:
                counter = int(last.split("_", 1)[1]) + 1
            except ValueError:
                counter = 1
        number = f"{prefix}_{counter:03d}"
        data["last_order_number"] = number
        self.save(data)
        return number
