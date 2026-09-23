from copy import deepcopy


FEATURE_DEFINITIONS = [
    ("has_letters", "Tem letras / nomes?"),
    ("has_full_letter_row", "Tem fila completa de letras?"),
    ("has_back_numbers", "Tem número das costas?"),
    ("has_front_numbers", "Tem número na frente?"),
    ("has_logos", "Tem logos / patrocinadores?"),
    ("has_complete_shirt", "Tem camisa completa?"),
]

ALL_FILES_LABEL = "Todos os arquivos"


CATEGORY_DEFINITIONS = {
    "camisa_completa": {
        "feature": "has_complete_shirt",
        "name": "Camisa Completa",
        "type": "all_files_from_folder",
        "extensions": [".tif", ".tiff"],
        "quick_action": True,
        "allow_group_add": False,
        "output_folder_name": "00_CAMISA_COMPLETA",
    },
    "letras": {
        "feature": "has_letters",
        "name": "Letras",
        "type": "individual_from_folder",
        "extensions": [".tif", ".tiff"],
        "item_label_regex": r"^([a-zA-Z])",
        "item_label_mode": "regex_first_group",
        "quick_action": False,
        "allow_group_add": True,
        "output_folder_name": "01_LETRAS",
    },
    "fila_completa_letras": {
        "feature": "has_full_letter_row",
        "name": "Fila Completa de Letras",
        "type": "individual_from_folder",
        "extensions": [".tif", ".tiff"],
        "item_label_regex": r"^([a-zA-Z])",
        "item_label_mode": "regex_first_group",
        "quick_action": True,
        "quick_action_all_files": True,
        "allow_group_add": True,
        "output_folder_name": "01_FILA_COMPLETA_LETRAS",
    },
    "numero_costas": {
        "feature": "has_back_numbers",
        "name": "Número Costas",
        "type": "individual_from_folder",
        "extensions": [".tif", ".tiff"],
        "item_label_regex": r"^(\d+)",
        "item_label_mode": "regex_first_group",
        "quick_action": False,
        "allow_group_add": True,
        "output_folder_name": "02_NUMEROS_COSTAS",
    },
    "numero_frente": {
        "feature": "has_front_numbers",
        "name": "Número Frente",
        "type": "individual_from_folder",
        "extensions": [".tif", ".tiff"],
        "item_label_regex": r"^(\d+)",
        "item_label_mode": "regex_first_group",
        "quick_action": False,
        "allow_group_add": True,
        "output_folder_name": "03_NUMEROS_FRENTE",
    },
    "logos": {
        "feature": "has_logos",
        "name": "Logos / Patrocinadores",
        "type": "individual_from_folder",
        "extensions": [".tif", ".tiff"],
        "quick_action": True,
        "quick_action_all_files": True,
        "allow_group_add": True,
        "output_folder_name": "04_LOGOS_PATROCINADORES",
    },
}


BLANK_CATALOG = {
    "schema_version": 1,
    "configured": False,
    "settings": {
        "default_output_folder": "",
        "allowed_extensions": [".tif", ".tiff"],
        "copy_mode": "duplicate_files",
        "open_folder_after_generate": True,
        "generate_txt_summary": True,
        "generate_cart_json": True,
    },
    "teams": [],
}


def default_features():
    return {key: False for key, _label in FEATURE_DEFINITIONS}


def make_category(category_id, folder_path="", enabled=True):
    category = deepcopy(CATEGORY_DEFINITIONS[category_id])
    category.update(
        {
            "id": category_id,
            "folder_path": folder_path or "",
            "enabled": bool(enabled),
        }
    )
    return category


def normalize_category(category):
    category_id = category.get("id")
    definition = CATEGORY_DEFINITIONS.get(category_id)
    if not definition:
        return category

    normalized = deepcopy(definition)
    normalized["id"] = category_id
    for key, value in category.items():
        if key in {"folder_path", "enabled", "name", "extensions", "output_folder_name"}:
            normalized[key] = value
        elif key not in normalized:
            normalized[key] = value
    return normalized


def categories_for_features(features, folder_paths=None):
    folder_paths = folder_paths or {}
    categories = []
    for category_id, definition in CATEGORY_DEFINITIONS.items():
        if features.get(definition["feature"], False):
            categories.append(make_category(category_id, folder_paths.get(category_id, "")))
    return categories


def category_label(category_id):
    return CATEGORY_DEFINITIONS.get(category_id, {}).get("name", category_id)
