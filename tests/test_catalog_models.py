import pytest

from src.models.catalog_models import BLANK_CATALOG, SCHEMA_VERSION, model_display_name


def test_schema_version_is_2_and_blank_catalog_uses_it():
    assert SCHEMA_VERSION == 2
    assert BLANK_CATALOG["schema_version"] == SCHEMA_VERSION


def test_display_name_with_season():
    assert model_display_name({"name": "Home 1", "season": 2026}) == "Home 1 · 2026"


@pytest.mark.parametrize("season", [None, "", True, "2026", 0])
def test_display_name_without_valid_season(season):
    assert model_display_name({"name": "Home 1", "season": season}) == "Home 1"


def test_display_name_without_season_key_or_name():
    assert model_display_name({"name": "Home 1"}) == "Home 1"
    assert model_display_name({}) == ""


def test_same_name_different_seasons_have_distinct_labels():
    labels = {
        model_display_name({"name": "Home 1", "season": 2025}),
        model_display_name({"name": "Home 1", "season": 2026}),
    }
    assert len(labels) == 2
