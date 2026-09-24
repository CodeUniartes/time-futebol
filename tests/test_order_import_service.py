import copy
import json
from pathlib import Path

import pytest

from src.services.order_import_service import (
    OrderImportError,
    validate_site_order,
)

EXAMPLE = json.loads(
    (Path(__file__).resolve().parents[1] / "contracts" / "order.example.json").read_text(encoding="utf-8")
)


def order(**changes):
    data = copy.deepcopy(EXAMPLE)
    data.update(changes)
    return data


def error_message(data):
    with pytest.raises(OrderImportError) as info:
        validate_site_order(data)
    return str(info.value)


def test_valid_order_passes():
    validate_site_order(order())


@pytest.mark.parametrize("data", [[], "texto", None, 3])
def test_not_an_object_is_invalid_file(data):
    assert error_message(data) == "Arquivo inválido: não é um pedido do site."


@pytest.mark.parametrize("version", [2, 0, "1", None, True])
def test_unsupported_version(version):
    assert error_message(order(schema_version=version)) == "Versão de pedido não suportada. Atualize o Montador."


def test_missing_version_is_unsupported():
    data = order()
    del data["schema_version"]
    assert error_message(data) == "Versão de pedido não suportada. Atualize o Montador."


@pytest.mark.parametrize("value", [None, "", "   ", 5])
def test_missing_code(value):
    assert error_message(order(code=value)) == "Pedido incompleto: falta `code`."


def test_missing_customer_name():
    assert error_message(order(customer={"whatsapp": "1"})) == "Pedido incompleto: falta `customer.name`."


def test_customer_not_an_object():
    assert error_message(order(customer="Fulano")) == "Pedido incompleto: falta `customer.name`."


@pytest.mark.parametrize("value", [None, [], "x"])
def test_missing_or_empty_items(value):
    assert error_message(order(items=value)) == "Pedido incompleto: falta `items`."


@pytest.mark.parametrize("field", ["team_id", "model_id", "category_id", "item_label"])
def test_item_missing_required_field(field):
    data = order()
    data["items"][0][field] = "  "
    assert error_message(data) == f"Pedido incompleto: falta `items[1].{field}`."


def test_item_not_an_object():
    assert error_message(order(items=["10"])) == "Pedido incompleto: falta `items[1]`."


@pytest.mark.parametrize("quantity", [0, -1, 1000, True, False, "2", 1.5, None])
def test_invalid_quantity(quantity):
    data = order()
    data["items"][0]["quantity"] = quantity
    assert error_message(data) == "Quantidade inválida no item `10`."


@pytest.mark.parametrize("quantity", [1, 999])
def test_quantity_limits_are_accepted(quantity):
    data = order()
    data["items"][0]["quantity"] = quantity
    validate_site_order(data)
