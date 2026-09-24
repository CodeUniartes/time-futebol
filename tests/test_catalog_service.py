import copy
import json
import time
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


@pytest.fixture
def team_id(service):
    return service.add_team("Atletico Mineiro")["id"]


def test_add_model_with_season_puts_year_in_id(service, team_id):
    model = service.add_model(team_id, "Home 1", season=2026)
    assert model["id"] == "home_1_2026"
    assert model["season"] == 2026
    assert model["active"] is True


def test_same_name_in_different_seasons_get_distinct_ids(service, team_id):
    first = service.add_model(team_id, "Home 1", season=2025)
    second = service.add_model(team_id, "Home 1", season=2026)
    assert first["id"] != second["id"]


def test_same_name_and_season_gets_numeric_suffix(service, team_id):
    service.add_model(team_id, "Home 1", season=2026)
    assert service.add_model(team_id, "Home 1", season=2026)["id"] == "home_1_2026_2"


def test_add_model_without_season_keeps_previous_behavior(service, team_id):
    model = service.add_model(team_id, "Home 1")
    assert model["id"] == "home_1"
    assert "season" not in model


def test_add_model_inactive(service, team_id):
    assert service.add_model(team_id, "Home 1", active=False)["active"] is False


@pytest.mark.parametrize("season", ["2026", True, 1.5])
def test_add_model_rejects_invalid_season(service, team_id, season):
    with pytest.raises(ValueError):
        service.add_model(team_id, "Home 1", season=season)


def test_update_model_sets_season_and_active_without_changing_id(service, team_id):
    model = service.add_model(team_id, "Home 1")
    updated = service.update_model(
        team_id, model["id"], "Home 1", "", default_features(), {}, season=2026, active=False
    )
    assert updated["id"] == "home_1"
    assert updated["season"] == 2026
    assert updated["active"] is False


def test_update_model_without_season_and_active_keeps_them(service, team_id):
    model = service.add_model(team_id, "Home 1", season=2026, active=False)
    updated = service.update_model(team_id, model["id"], "Home 1 novo", "", default_features(), {})
    assert updated["season"] == 2026
    assert updated["active"] is False
    assert updated["name"] == "Home 1 novo"


def test_update_model_can_clear_season(service, team_id):
    model = service.add_model(team_id, "Home 1", season=2026)
    updated = service.update_model(team_id, model["id"], "Home 1", "", default_features(), {}, season=None)
    assert "season" not in updated


def test_save_catalog_writes_updated_at_in_utc(tmp_path):
    moment = datetime(2026, 9, 24, 12, 30, 15, 123000, tzinfo=timezone.utc)
    service = CatalogService(catalog_path=tmp_path / "catalogo.json", clock=lambda: moment)
    service.save_catalog(service.load_catalog())
    saved = json.loads((tmp_path / "catalogo.json").read_text(encoding="utf-8"))
    assert saved["updated_at"] == "2026-09-24T12:30:15.123Z"


def test_updated_at_changes_on_every_save(service):
    service.save_catalog(service.load_catalog())
    first = service.load_catalog()["updated_at"]
    time.sleep(0.005)
    service.save_catalog(service.load_catalog())
    second = service.load_catalog()["updated_at"]
    assert first.endswith("Z") and second.endswith("Z")
    assert second > first


def test_every_write_goes_through_save_catalog(service, team_id):
    service.add_model(team_id, "Home 1")
    assert service.load_catalog()["updated_at"].endswith("Z")
