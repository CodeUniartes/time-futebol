import copy
import json
from datetime import datetime, timezone

import pytest

from src.models.catalog_models import default_features
from src.services.catalog_service import CatalogService

V1_CATALOG = {
    "schema_version": 1,
    "configured": True,
    "settings": {"default_output_folder": "D:/pedidos"},
    "teams": [
        {
            "id": "atletico_mineiro",
            "name": "Atletico Mineiro",
            "models": [
                {
                    "id": "home_1",
                    "name": "Home 1",
                    "description": "camisa branca",
                    "features": {**default_features(), "has_back_numbers": True},
                    "categories": [
                        {"id": "numero_costas", "folder_path": "D:/galo/numeros", "enabled": True}
                    ],
                }
            ],
        }
    ],
}


def write_catalog(tmp_path, data):
    path = tmp_path / "catalogo.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def service(tmp_path):
    return CatalogService(catalog_path=tmp_path / "catalogo.json")


def test_v1_catalog_loads_as_v2_without_losing_data_or_changing_ids(tmp_path):
    original = copy.deepcopy(V1_CATALOG)
    catalog = CatalogService(catalog_path=write_catalog(tmp_path, original)).load_catalog()

    assert catalog["schema_version"] == 2
    team = catalog["teams"][0]
    model = team["models"][0]
    assert (team["id"], model["id"]) == ("atletico_mineiro", "home_1")
    assert model["description"] == "camisa branca"
    assert model["features"]["has_back_numbers"] is True
    assert model["categories"][0]["folder_path"] == "D:/galo/numeros"
    assert catalog["settings"]["default_output_folder"] == "D:/pedidos"
    assert model["active"] is True
    assert "season" not in model


def test_migration_is_in_memory_until_next_save(tmp_path):
    path = write_catalog(tmp_path, copy.deepcopy(V1_CATALOG))
    service = CatalogService(catalog_path=path)
    service.load_catalog()
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1


def test_v2_catalog_keeps_active_false_and_season(tmp_path):
    data = copy.deepcopy(V1_CATALOG)
    data["schema_version"] = 2
    data["teams"][0]["models"][0].update(active=False, season=2025)
    model = CatalogService(catalog_path=write_catalog(tmp_path, data)).load_catalog()["teams"][0]["models"][0]
    assert model["active"] is False
    assert model["season"] == 2025
