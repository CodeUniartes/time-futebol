MAX_QUANTITY = 999
SUPPORTED_SCHEMA_VERSION = 1
ITEM_REQUIRED_FIELDS = ("team_id", "model_id", "category_id", "item_label")


class OrderImportError(Exception):
    pass


def validate_site_order(data):
    if not isinstance(data, dict):
        raise OrderImportError("Arquivo inválido: não é um pedido do site.")

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
