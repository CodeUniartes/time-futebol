import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from src.models.catalog_models import ALL_FILES_LABEL

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


@pytest.fixture
def catalog_validator():
    schema = load("catalog.public.schema.json")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def all_items(catalog):
    for team in catalog["teams"]:
        for model in team["models"]:
            for category in model["categories"]:
                for item in category["items"]:
                    yield category, item


def test_public_catalog_example_matches_schema(catalog_validator):
    assert list(catalog_validator.iter_errors(load("catalog.public.example.json"))) == []


def test_public_catalog_example_has_versions_and_an_item():
    catalog = load("catalog.public.example.json")
    assert catalog["schema_version"] == 1
    assert catalog["catalog_version"].endswith("Z")
    assert next(all_items(catalog), None) is not None


def test_public_catalog_example_shows_size_and_all_files_item():
    catalog = load("catalog.public.example.json")
    assert any("width_cm" in item and "height_cm" in item for _category, item in all_items(catalog))
    all_files = [category for category, _item in all_items(catalog) if category.get("all_files_option")]
    assert all_files
    assert all(item["label"] == ALL_FILES_LABEL for category in all_files for item in category["items"])


def test_public_catalog_previews_are_relative_webp_paths():
    for _category, item in all_items(load("catalog.public.example.json")):
        assert item["preview"].startswith("previews/")
        assert item["preview"].endswith(".webp")
        assert ".." not in item["preview"]


@pytest.mark.parametrize("missing", ["schema_version", "catalog_version", "teams"])
def test_public_catalog_schema_requires_root_fields(catalog_validator, missing):
    catalog = load("catalog.public.example.json")
    del catalog[missing]
    assert list(catalog_validator.iter_errors(catalog))


def test_public_catalog_schema_rejects_non_positive_size(catalog_validator):
    catalog = load("catalog.public.example.json")
    next(all_items(catalog))[1]["width_cm"] = 0
    assert list(catalog_validator.iter_errors(catalog))


def test_public_catalog_schema_accepts_unknown_fields(catalog_validator):
    catalog = load("catalog.public.example.json")
    catalog["foo"] = 1
    next(all_items(catalog))[1]["bar"] = 2
    assert list(catalog_validator.iter_errors(catalog)) == []


def test_contracts_readme_documents_versioning():
    text = (CONTRACTS_DIR / "README.md").read_text(encoding="utf-8")
    assert "schema_version" in text
    assert "opcional" in text
