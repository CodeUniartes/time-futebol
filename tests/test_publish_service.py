import json
import os
from pathlib import Path

import numpy as np
import pytest
import tifffile
from jsonschema import Draft202012Validator
from PIL import Image

from src.models.catalog_models import ALL_FILES_LABEL, default_features, make_category
from src.services.catalog_service import CatalogService
from src.services.publish_service import PublishService
from src.services.site_config_service import SiteConfigService

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "contracts" / "catalog.public.schema.json").read_text(encoding="utf-8")
)


def make_tif(path, width=354, height=591, dpi=300, box=None, corrupt=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if corrupt:
        path.write_bytes(b"isto nao e um tiff")
        return path
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    x0, y0, x1, y1 = box or (0, 0, width, height)
    rgba[y0:y1, x0:x1] = (200, 30, 30, 255)
    kwargs = {"resolution": (dpi, dpi), "resolutionunit": "INCH"} if dpi else {"resolution": None}
    tifffile.imwrite(path, rgba, photometric="rgb", extrasamples=["unassalpha"], planarconfig="contig", **kwargs)
    return path


@pytest.fixture
def env(tmp_path):
    catalog_service = CatalogService(catalog_path=tmp_path / "config" / "catalogo.json")
    site = SiteConfigService(config_path=tmp_path / "config" / "site.json", app_root=tmp_path)
    return {"tmp": tmp_path, "catalog": catalog_service, "site": site, "service": PublishService(catalog_service, site)}


def add_shirt(env, categories, active=True, season=2026, team_id="galo", model_id="home_1"):
    catalog = env["catalog"].load_catalog()
    team = next((t for t in catalog["teams"] if t["id"] == team_id), None)
    if team is None:
        team = {"id": team_id, "name": team_id.title(), "models": []}
        catalog["teams"].append(team)
    team["models"].append(
        {
            "id": model_id,
            "name": "Home 1",
            "season": season,
            "description": "",
            "active": active,
            "features": default_features(),
            "categories": categories,
        }
    )
    catalog["configured"] = True
    env["catalog"].save_catalog(catalog)


def numbers_category(folder, enabled=True):
    return make_category("numero_costas", str(folder), enabled)


def published(env):
    return json.loads((env["site"].publish_dir() / "catalog.public.json").read_text(encoding="utf-8"))


def items_of(catalog, category_id):
    for team in catalog["teams"]:
        for model in team["models"]:
            for category in model["categories"]:
                if category["id"] == category_id:
                    return category["items"]
    return None


def preview_files(env):
    return sorted((env["site"].publish_dir() / "previews").rglob("*.webp"))


def test_publishes_items_with_size_and_preview(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10 Galo.tif", width=1181, height=2953)
    make_tif(folder / "7 Galo.tif", width=1050, height=2953)
    add_shirt(env, [numbers_category(folder)])

    result = env["service"].publish()
    catalog = published(env)

    assert list(Draft202012Validator(SCHEMA).iter_errors(catalog)) == []
    assert catalog["catalog_version"] == env["catalog"].load_catalog()["updated_at"]
    items = items_of(catalog, "numero_costas")
    assert [item["label"] for item in items] == ["7", "10"]
    assert (items[1]["width_cm"], items[1]["height_cm"]) == (10.0, 25.0)
    assert items[1]["preview"] == "previews/galo/home_1/numero_costas/10.webp"
    with Image.open(env["site"].publish_dir() / items[1]["preview"]) as preview:
        assert preview.format == "WEBP"
        assert max(preview.size) <= 400
    assert (result.generated, result.reused, result.failures, result.cancelled) == (2, 0, [], False)


def test_model_and_category_fields_follow_the_contract(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    add_shirt(env, [numbers_category(folder)])
    env["service"].publish()
    model = published(env)["teams"][0]["models"][0]
    assert (model["id"], model["name"], model["season"]) == ("home_1", "Home 1", 2026)
    category = model["categories"][0]
    assert (category["id"], category["allow_group_add"], category["all_files_option"]) == ("numero_costas", True, False)


def test_inactive_shirt_disabled_category_and_missing_folder_are_left_out(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    (env["tmp"] / "vazia").mkdir()
    add_shirt(env, [numbers_category(folder)], active=False, model_id="inativa")
    add_shirt(env, [numbers_category(folder, enabled=False)], model_id="desabilitada")
    add_shirt(env, [numbers_category(env["tmp"] / "nao_existe")], model_id="sem_pasta")
    add_shirt(env, [numbers_category(env["tmp"] / "vazia")], model_id="vazia")
    add_shirt(env, [numbers_category(folder)], model_id="ok")

    env["service"].publish()
    models = [model["id"] for team in published(env)["teams"] for model in team["models"]]
    assert models == ["ok"]


def test_team_without_items_is_left_out(env):
    add_shirt(env, [numbers_category(env["tmp"] / "nada")], team_id="time_vazio")
    env["service"].publish()
    assert published(env)["teams"] == []


def test_all_files_category_exposes_single_item_with_pieces(env):
    folder = env["tmp"] / "camisa"
    make_tif(folder / "frente.tif", width=1417, height=1772)
    make_tif(folder / "costas.tif", width=1181, height=1181)
    add_shirt(env, [make_category("camisa_completa", str(folder))])

    env["service"].publish()
    catalog = published(env)
    assert list(Draft202012Validator(SCHEMA).iter_errors(catalog)) == []
    items = items_of(catalog, "camisa_completa")
    assert [item["label"] for item in items] == [ALL_FILES_LABEL]
    assert items[0]["pieces"] == [{"width_cm": 10.0, "height_cm": 10.0}, {"width_cm": 12.0, "height_cm": 15.0}]
    assert "width_cm" not in items[0]
    category = catalog["teams"][0]["models"][0]["categories"][0]
    assert category["all_files_option"] is True
    assert (env["site"].publish_dir() / items[0]["preview"]).exists()


def test_individual_category_with_quick_action_gets_extra_all_files_item(env):
    folder = env["tmp"] / "fila"
    make_tif(folder / "A Galo.tif")
    make_tif(folder / "B Galo.tif")
    add_shirt(env, [make_category("fila_completa_letras", str(folder))])

    env["service"].publish()
    items = items_of(published(env), "fila_completa_letras")
    assert [item["label"] for item in items] == ["A", "B", ALL_FILES_LABEL]
    assert len(items[-1]["pieces"]) == 2
    assert items[0]["width_cm"] > 0


def test_unreadable_file_is_omitted_and_reported(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    make_tif(folder / "11.tif", corrupt=True)
    add_shirt(env, [numbers_category(folder)])

    result = env["service"].publish()
    assert [item["label"] for item in items_of(published(env), "numero_costas")] == ["10"]
    assert len(result.failures) == 1
    assert "11.tif" in result.failures[0]
    assert "11.tif" in (env["site"].publish_dir() / "relatorio.txt").read_text(encoding="utf-8")


def test_second_run_reuses_everything(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    make_tif(folder / "7.tif")
    add_shirt(env, [numbers_category(folder)])
    env["service"].publish()
    result = env["service"].publish()
    assert (result.generated, result.reused) == (0, 2)


def test_changed_file_regenerates_only_that_item(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    make_tif(folder / "7.tif")
    add_shirt(env, [numbers_category(folder)])
    env["service"].publish()
    make_tif(folder / "10.tif", width=800, height=1200)
    os.utime(folder / "10.tif", (1_900_000_000, 1_900_000_000))
    result = env["service"].publish()
    assert (result.generated, result.reused) == (1, 1)


def test_new_watermark_regenerates_everything(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    add_shirt(env, [numbers_category(folder)])
    env["service"].publish()
    (env["tmp"] / "config" / "site.json").write_text(json.dumps({"watermark": {"text": "OUTRA"}}), encoding="utf-8")
    assert env["service"].publish().generated == 1


def test_removed_item_deletes_its_preview(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    make_tif(folder / "7.tif")
    add_shirt(env, [numbers_category(folder)])
    env["service"].publish()
    assert len(preview_files(env)) == 2
    (folder / "7.tif").unlink()
    env["service"].publish()
    assert [p.name for p in preview_files(env)] == ["10.webp"]


def test_labels_with_the_same_slug_get_unique_paths(env):
    folder = env["tmp"] / "logos"
    make_tif(folder / "Logo A B.tif")
    make_tif(folder / "Logo-A-B.tif")
    add_shirt(env, [make_category("logos", str(folder))])
    env["service"].publish()
    previews = [item["preview"] for item in items_of(published(env), "logos") if item["label"] != ALL_FILES_LABEL]
    assert len(previews) == 2 and len(set(previews)) == 2
    assert all(env["site"].publish_dir().joinpath(p).exists() for p in previews)


def test_assumed_dpi_is_a_warning(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif", dpi=None)
    add_shirt(env, [numbers_category(folder)])
    result = env["service"].publish()
    assert any("dpi" in warning.lower() and "10.tif" in warning for warning in result.warnings)


def test_art_that_does_not_fit_the_film_in_any_orientation_is_a_warning(env):
    folder = env["tmp"] / "logos"
    make_tif(folder / "Enorme.tif", width=2400, height=2800, dpi=100)  # 61 x 71 cm
    add_shirt(env, [make_category("logos", str(folder))])
    result = env["service"].publish()
    assert any("58" in warning and "Enorme" in warning for warning in result.warnings)


def test_wide_strip_that_fits_rotated_is_not_a_warning(env):
    folder = env["tmp"] / "logos"
    make_tif(folder / "Faixa.tif", width=7200, height=300)  # 61 x 2,5 cm: cabe girada
    add_shirt(env, [make_category("logos", str(folder))])
    assert not any("58" in warning for warning in env["service"].publish().warnings)


def test_catalog_without_updated_at_is_saved_first(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    add_shirt(env, [numbers_category(folder)])
    raw = json.loads(env["catalog"].catalog_path.read_text(encoding="utf-8"))
    del raw["updated_at"]
    env["catalog"].catalog_path.write_text(json.dumps(raw), encoding="utf-8")
    env["service"].publish()
    assert published(env)["catalog_version"].endswith("Z")


def test_progress_reports_every_file(env):
    folder = env["tmp"] / "numeros"
    for name in ("1", "2", "3"):
        make_tif(folder / f"{name}.tif")
    add_shirt(env, [numbers_category(folder)])
    calls = []
    env["service"].publish(progress=lambda done, total, message: calls.append((done, total)))
    assert calls[-1] == (3, 3)
    assert [done for done, _ in calls] == sorted(done for done, _ in calls)


def test_cancel_keeps_the_previous_catalog_untouched(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    add_shirt(env, [numbers_category(folder)])
    env["service"].publish()
    before = (env["site"].publish_dir() / "catalog.public.json").read_text(encoding="utf-8")
    make_tif(folder / "11.tif")
    result = env["service"].publish(cancel=lambda: True)
    assert result.cancelled is True
    assert (env["site"].publish_dir() / "catalog.public.json").read_text(encoding="utf-8") == before


def test_output_folder_layout(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "10.tif")
    add_shirt(env, [numbers_category(folder)])
    env["service"].publish()
    names = {p.name for p in env["site"].publish_dir().iterdir()}
    assert {"catalog.public.json", "previews", "relatorio.txt", ".cache.json"} <= names
    assert "cache" not in json.dumps(published(env)).lower()


def test_progress_reaches_total_even_when_a_file_fails(env):
    folder = env["tmp"] / "numeros"
    make_tif(folder / "1.tif")
    make_tif(folder / "2.tif", corrupt=True)
    add_shirt(env, [numbers_category(folder)])
    calls = []
    env["service"].publish(progress=lambda done, total, message: calls.append((done, total)))
    assert calls[-1] == (2, 2)


def test_second_run_does_not_read_any_tiff_again(env, monkeypatch):
    folder = env["tmp"] / "fila"
    make_tif(folder / "A Galo.tif")
    make_tif(folder / "B Galo.tif")
    add_shirt(env, [make_category("fila_completa_letras", str(folder))])
    env["service"].publish()

    from src.services import publish_service

    reads = []
    original = publish_service.read_tiff
    monkeypatch.setattr(publish_service, "read_tiff", lambda path: reads.append(path) or original(path))
    result = env["service"].publish()
    assert reads == []
    assert (result.generated, result.reused) == (0, 3)


def test_changing_one_file_regenerates_the_all_files_item(env):
    folder = env["tmp"] / "fila"
    make_tif(folder / "A Galo.tif")
    make_tif(folder / "B Galo.tif")
    add_shirt(env, [make_category("fila_completa_letras", str(folder))])
    env["service"].publish()
    make_tif(folder / "B Galo.tif", width=800, height=900)
    os.utime(folder / "B Galo.tif", (1_900_000_000, 1_900_000_000))
    result = env["service"].publish()
    assert (result.generated, result.reused) == (2, 1)
    assert items_of(published(env), "fila_completa_letras")[-1]["pieces"][1]["width_cm"] == 6.8
