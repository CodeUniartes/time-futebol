import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

CONTRACTS_DIR = Path(__file__).resolve().parents[1] / "contracts"


def load(name):
    return json.loads((CONTRACTS_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture
def order_validator():
    schema = load("order.schema.json")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def valid_order():
    return load("order.example.json")


def test_order_example_matches_schema(order_validator):
    assert list(order_validator.iter_errors(valid_order())) == []


def test_order_schema_accepts_unknown_fields(order_validator):
    order = valid_order()
    order["foo"] = "bar"
    order["items"][0]["custom"] = {"name": "Fulano", "number": 10}
    assert list(order_validator.iter_errors(order)) == []


@pytest.mark.parametrize("missing", ["code", "customer", "items", "schema_version"])
def test_order_schema_requires_root_fields(order_validator, missing):
    order = valid_order()
    del order[missing]
    assert list(order_validator.iter_errors(order))


def test_order_schema_requires_customer_name(order_validator):
    order = valid_order()
    del order["customer"]["name"]
    assert list(order_validator.iter_errors(order))


def test_order_schema_rejects_empty_items(order_validator):
    order = valid_order()
    order["items"] = []
    assert list(order_validator.iter_errors(order))


@pytest.mark.parametrize("field", ["team_id", "model_id", "category_id", "item_label", "quantity"])
def test_order_schema_requires_item_fields(order_validator, field):
    order = valid_order()
    del order["items"][0][field]
    assert list(order_validator.iter_errors(order))


@pytest.mark.parametrize("quantity", [0, 1000, True, "2", 1.5])
def test_order_schema_rejects_invalid_quantity(order_validator, quantity):
    order = valid_order()
    order["items"][0]["quantity"] = quantity
    assert list(order_validator.iter_errors(order))


def test_order_schema_rejects_unknown_version(order_validator):
    order = valid_order()
    order["schema_version"] = 2
    assert list(order_validator.iter_errors(order))
