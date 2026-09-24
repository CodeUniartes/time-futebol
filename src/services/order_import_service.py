import json
from dataclasses import dataclass, field

from src.models.cart_models import CartItem
from src.services.catalog_lookup import find_in_catalog

MAX_QUANTITY = 999
SUPPORTED_SCHEMA_VERSION = 1
ITEM_REQUIRED_FIELDS = ("team_id", "model_id", "category_id", "item_label")


INVALID_FILE_MESSAGE = "Arquivo inválido: não é um pedido do site."


class OrderImportError(Exception):
    pass


@dataclass
class ImportedOrder:
    payload: dict
    warnings: list = field(default_factory=list)


def parse_site_order_file(path, catalog):
    try:
        with open(path, "r", encoding="utf-8-sig") as file:
            text = file.read()
    except (OSError, UnicodeDecodeError) as error:
        raise OrderImportError(INVALID_FILE_MESSAGE) from error
    return parse_site_order_text(text, catalog)


def parse_site_order_text(text, catalog):
    try:
        data = json.loads(text)
    except ValueError as error:
        raise OrderImportError(INVALID_FILE_MESSAGE) from error
    return parse_site_order(data, catalog)


def parse_site_order(data, catalog):
    validate_site_order(data)
    cart_items = [_cart_item(item) for item in data["items"]]
    first = cart_items[0]
    payload = {
        "order": {
            "cliente": data["customer"]["name"].strip(),
            "numero_pedido": data["code"].strip(),
            "observacao": _observation(data),
        },
        "selected_team_id": first.team_id,
        "selected_model_id": first.model_id,
        "items": [item.to_dict() for item in cart_items],
    }
    return ImportedOrder(payload=payload, warnings=_catalog_warnings(cart_items, catalog))


def validate_site_order(data):
    if not isinstance(data, dict):
        raise OrderImportError(INVALID_FILE_MESSAGE)

    version = data.get("schema_version")
    # bool é subclasse de int: True == 1 passaria sem essa checagem
    if isinstance(version, bool) or version != SUPPORTED_SCHEMA_VERSION:
        raise OrderImportError("Versão de pedido não suportada. Atualize o Montador.")

    if not _filled(data.get("code")):
        raise _missing("code")

    customer = data.get("customer")
    if not isinstance(customer, dict) or not _filled(customer.get("name")):
        raise _missing("customer.name")

    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise _missing("items")

    for position, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise _missing(f"items[{position}]")
        for field in ITEM_REQUIRED_FIELDS:
            if not _filled(item.get(field)):
                raise _missing(f"items[{position}].{field}")
        if not _valid_quantity(item.get("quantity")):
            raise OrderImportError(f"Quantidade inválida no item `{item['item_label'].strip()}`.")


def _filled(value):
    return isinstance(value, str) and bool(value.strip())


def _valid_quantity(value):
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= MAX_QUANTITY


def _missing(field):
    return OrderImportError(f"Pedido incompleto: falta `{field}`.")


def _cart_item(item):
    team_id = item["team_id"].strip()
    model_id = item["model_id"].strip()
    category_id = item["category_id"].strip()
    model_name = _text(item.get("model_name")) or model_id
    season = item.get("season")
    if isinstance(season, int) and not isinstance(season, bool):
        model_name = f"{model_name} · {season}"
    return CartItem(
        team_id=team_id,
        team_name=_text(item.get("team_name")) or team_id,
        model_id=model_id,
        model_name=model_name,
        category_id=category_id,
        category_name=_text(item.get("category_name")) or category_id,
        item_label=item["item_label"].strip(),
        quantity=item["quantity"],
    )


def _observation(data):
    customer = data["customer"]
    whatsapp = _text(customer.get("whatsapp"))
    parts = [f"WhatsApp {whatsapp}" if whatsapp else "", _text(data.get("note"))]
    return " · ".join(part for part in parts if part)


def _catalog_warnings(cart_items, catalog):
    catalog = catalog or {}
    missing = [item for item in cart_items if not find_in_catalog(catalog, item)]
    if not missing:
        return []
    described = "; ".join(
        f"{item.team_name} / {item.model_name} / {item.category_name} / {item.item_label}" for item in missing
    )
    return [f"Itens fora do catálogo local (entram no carrinho e ficam em arquivos_faltando.txt): {described}."]


def _text(value):
    return value.strip() if isinstance(value, str) else ""
