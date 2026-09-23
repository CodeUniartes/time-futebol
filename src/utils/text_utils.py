import re
import unicodedata


def normalize_spaces(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value, fallback="sem_nome"):
    text = normalize_spaces(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text or fallback


def safe_filename(value, fallback="pedido"):
    text = normalize_spaces(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r'[<>:"/\\|?*\x00-\x1F]+', "_", text)
    text = re.sub(r"\s+", "_", text).strip("._ ")
    return text or fallback


def parse_comma_items(value):
    return [item.strip() for item in str(value or "").split(",") if item.strip()]
