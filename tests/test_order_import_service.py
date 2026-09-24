import copy
import json
from pathlib import Path

import pytest

from src.services.order_import_service import (
    ImportedOrder,
    OrderImportError,
    parse_site_order,
    parse_site_order_file,
    parse_site_order_text,
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


CATALOG = {
    "teams": [
        {
            "id": "atletico_mineiro",
            "name": "Atletico Mineiro",
            "models": [
                {
                    "id": "home_1_2026",
                    "name": "Home 1",
                    "categories": [{"id": "numero_costas", "name": "Número Costas"}],
                }
            ],
        }
    ]
}


def parsed(data=None, catalog=CATALOG):
    return parse_site_order(data if data is not None else order(), catalog)


def test_parse_returns_payload_for_order_panel():
    result = parsed()
    assert isinstance(result, ImportedOrder)
    payload = result.payload
    assert payload["order"] == {
        "cliente": "Fulano",
        "numero_pedido": "DTF-7K3F",
        "observacao": "WhatsApp 31999999999 · Entrega sexta",
    }
    assert payload["selected_team_id"] == "atletico_mineiro"
    assert payload["selected_model_id"] == "home_1_2026"
    assert payload["items"] == [
        {
            "team_id": "atletico_mineiro",
            "team_name": "Atletico Mineiro",
            "model_id": "home_1_2026",
            "model_name": "Home 1 · 2026",
            "category_id": "numero_costas",
            "category_name": "Número Costas",
            "item_label": "10",
            "quantity": 2,
        }
    ]
    assert result.warnings == []


def test_observation_without_whatsapp():
    data = order(customer={"name": "Fulano"})
    assert parsed(data).payload["order"]["observacao"] == "Entrega sexta"


def test_observation_without_note():
    data = order()
    del data["note"]
    assert parsed(data).payload["order"]["observacao"] == "WhatsApp 31999999999"


def test_observation_empty_when_no_whatsapp_and_no_note():
    data = order(customer={"name": "Fulano"})
    del data["note"]
    assert parsed(data).payload["order"]["observacao"] == ""


def test_model_name_without_season_is_kept():
    data = order()
    del data["items"][0]["season"]
    assert parsed(data).payload["items"][0]["model_name"] == "Home 1"


def test_missing_names_fall_back_to_ids():
    data = order()
    for field in ("team_name", "model_name", "category_name"):
        del data["items"][0][field]
    item = parsed(data).payload["items"][0]
    assert item["team_name"] == "atletico_mineiro"
    assert item["model_name"] == "home_1_2026 · 2026"
    assert item["category_name"] == "numero_costas"


def test_selected_team_and_model_come_from_first_item():
    data = order()
    second = copy.deepcopy(data["items"][0])
    second.update(team_id="cruzeiro", model_id="azul_2026")
    data["items"].append(second)
    payload = parsed(data).payload
    assert payload["selected_team_id"] == "atletico_mineiro"
    assert payload["selected_model_id"] == "home_1_2026"
    assert len(payload["items"]) == 2


def test_unknown_fields_are_ignored_and_not_in_payload():
    data = order(foo="bar")
    data["items"][0]["custom"] = {"name": "Fulano", "number": 10}
    result = parsed(data)
    assert "foo" not in result.payload
    assert "custom" not in result.payload["items"][0]
    assert result.warnings == []


def test_item_outside_catalog_becomes_warning_and_stays_in_cart():
    data = order()
    data["items"][0]["category_id"] = "logos"
    data["items"][0]["category_name"] = "Logos"
    result = parsed(data)
    assert len(result.payload["items"]) == 1
    assert len(result.warnings) == 1
    assert "Atletico Mineiro" in result.warnings[0]
    assert "Logos" in result.warnings[0]
    assert "10" in result.warnings[0]


def test_empty_catalog_warns_about_every_item():
    assert len(parsed(catalog={"teams": []}).warnings) == 1
    assert len(parsed(catalog=None).warnings) == 1


def test_invalid_order_raises_before_mapping():
    with pytest.raises(OrderImportError):
        parsed(order(items=[]))


def test_parse_text_rejects_invalid_json():
    with pytest.raises(OrderImportError) as info:
        parse_site_order_text("{ isso não é json", CATALOG)
    assert str(info.value) == "Arquivo inválido: não é um pedido do site."


def test_parse_file_reads_utf8_with_bom(tmp_path):
    path = tmp_path / "pedido.json"
    path.write_text(json.dumps(EXAMPLE, ensure_ascii=False), encoding="utf-8-sig")
    assert parse_site_order_file(path, CATALOG).payload["order"]["numero_pedido"] == "DTF-7K3F"


def test_parse_file_rejects_binary_and_missing_files(tmp_path):
    binary = tmp_path / "pedido.json"
    binary.write_bytes(bytes([0xFF, 0xFE, 0x00, 0x81]))
    for path in (binary, tmp_path / "nao_existe.json"):
        with pytest.raises(OrderImportError) as info:
            parse_site_order_file(path, CATALOG)
        assert str(info.value) == "Arquivo inválido: não é um pedido do site."


def test_repository_example_is_accepted_by_parser():
    assert parse_site_order(EXAMPLE, CATALOG).payload["order"]["cliente"] == "Fulano"
