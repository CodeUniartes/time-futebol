import re
from pathlib import Path


def natural_key(value):
    parts = re.split(r"(\d+)", str(value))
    return [int(part) if part.isdigit() else part.casefold() for part in parts]


def accepted_files(folder_path, extensions):
    folder = Path(folder_path or "")
    if not folder.exists() or not folder.is_dir():
        return []
    allowed = {ext.casefold() for ext in (extensions or [".tif", ".tiff"])}
    files = [path for path in folder.iterdir() if path.is_file() and path.suffix.casefold() in allowed]
    return sorted(files, key=lambda path: natural_key(path.name))


def extract_item_label(path, category):
    pattern = category.get("item_label_regex")
    stem = Path(path).stem
    if pattern:
        match = re.search(pattern, stem, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return stem.strip()


def build_item_index(category):
    index = {}
    for path in accepted_files(category.get("folder_path", ""), category.get("extensions")):
        label = extract_item_label(path, category)
        if not label:
            continue
        key = label.casefold()
        index.setdefault(key, {"label": label, "path": path})
    return index


def list_available_items(category):
    index = build_item_index(category)
    labels = [entry["label"] for entry in index.values()]
    return sorted(labels, key=natural_key)


def find_item_file(category, item_label):
    item_label = str(item_label or "").strip()
    if not item_label:
        return None
    index = build_item_index(category)
    entry = index.get(item_label.casefold())
    if entry:
        return entry["path"]

    for path in accepted_files(category.get("folder_path", ""), category.get("extensions")):
        stem = path.stem.casefold()
        if stem.startswith(item_label.casefold()):
            return path
    return None
