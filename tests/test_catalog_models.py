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


from src.models.catalog_models import model_menu_map, parse_season


def test_menu_map_uses_display_names():
    models = [
        {"id": "home_1_2025", "name": "Home 1", "season": 2025},
        {"id": "home_1_2026", "name": "Home 1", "season": 2026},
    ]
    assert model_menu_map(models) == {"Home 1 · 2025": "home_1_2025", "Home 1 · 2026": "home_1_2026"}


def test_menu_map_keeps_identical_labels_apart():
    models = [{"id": "a", "name": "Home"}, {"id": "b", "name": "Home"}, {"id": "c", "name": "Home"}]
    result = model_menu_map(models)
    assert sorted(result.values()) == ["a", "b", "c"]
    assert len(result) == 3
    assert list(result)[0] == "Home"


@pytest.mark.parametrize("text, expected", [("", None), ("  ", None), ("2026", 2026), (" 1999 ", 1999)])
def test_parse_season_accepts(text, expected):
    assert parse_season(text) == expected


@pytest.mark.parametrize("text", ["26", "abc", "20 26", "1899", "2101", "-2026", "2026.5"])
def test_parse_season_rejects(text):
    with pytest.raises(ValueError):
        parse_season(text)
