from pathlib import Path

from src.utils.json_utils import load_json
from src.utils.path_utils import APP_ROOT, CONFIG_DIR
from src.utils.preview_image import PREVIEW_MAX_SIDE, Watermark

DEFAULT_PUBLISH_DIR = "publish"


class SiteConfigService:
    """Lê config/site.json (ignorado pelo git). Sem arquivo ou com valor inválido, usa os padrões."""

    def __init__(self, config_path=None, app_root=None):
        self.config_path = Path(config_path) if config_path else CONFIG_DIR / "site.json"
        self.app_root = Path(app_root) if app_root else APP_ROOT

    def _load(self):
        try:
            data = load_json(self.config_path, {})
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def watermark(self):
        defaults = Watermark()
        raw = self._load().get("watermark")
        raw = raw if isinstance(raw, dict) else {}
        text = raw.get("text")
        text = text.strip() if isinstance(text, str) else ""
        return Watermark(
            text=text or defaults.text,
            opacity=_clamped_number(raw.get("opacity"), defaults.opacity, 0.0, 1.0),
            angle=_number(raw.get("angle"), defaults.angle),
        )

    def publish_dir(self):
        value = self._load().get("publish_dir")
        path = Path(value) if isinstance(value, str) and value.strip() else Path(DEFAULT_PUBLISH_DIR)
        return path if path.is_absolute() else self.app_root / path

    def preview_max_side(self):
        value = self._load().get("preview_max_side")
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
        return PREVIEW_MAX_SIDE


def _number(value, default):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return float(default)
    return float(value)


def _clamped_number(value, default, low, high):
    return min(max(_number(value, default), low), high)
