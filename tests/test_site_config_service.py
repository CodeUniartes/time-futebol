import json

from src.services.site_config_service import SiteConfigService
from src.utils.preview_image import Watermark


def service(tmp_path, data=None):
    path = tmp_path / "site.json"
    if data is not None:
        path.write_text(json.dumps(data), encoding="utf-8")
    return SiteConfigService(config_path=path, app_root=tmp_path)


def test_defaults_when_file_is_missing(tmp_path):
    config = service(tmp_path)
    assert config.watermark() == Watermark(text="UNIARTES", opacity=0.25, angle=30.0)
    assert config.publish_dir() == tmp_path / "publish"
    assert config.preview_max_side() == 400


def test_missing_file_is_not_created(tmp_path):
    service(tmp_path).watermark()
    assert not (tmp_path / "site.json").exists()


def test_overrides_from_file(tmp_path):
    config = service(
        tmp_path,
        {"watermark": {"text": "MINHA MARCA", "opacity": 0.4, "angle": 45}, "publish_dir": "saida", "preview_max_side": 300},
    )
    assert config.watermark() == Watermark(text="MINHA MARCA", opacity=0.4, angle=45.0)
    assert config.publish_dir() == tmp_path / "saida"
    assert config.preview_max_side() == 300


def test_absolute_publish_dir_is_kept(tmp_path):
    target = tmp_path / "fora" / "publicar"
    assert service(tmp_path, {"publish_dir": str(target)}).publish_dir() == target


def test_invalid_values_fall_back_to_defaults(tmp_path):
    config = service(
        tmp_path, {"watermark": {"text": "", "opacity": "muito", "angle": None}, "preview_max_side": -5}
    )
    assert config.watermark() == Watermark(text="UNIARTES", opacity=0.25, angle=30.0)
    assert config.preview_max_side() == 400


def test_opacity_is_clamped_between_zero_and_one(tmp_path):
    assert service(tmp_path, {"watermark": {"opacity": 7}}).watermark().opacity == 1.0
    assert service(tmp_path, {"watermark": {"opacity": -1}}).watermark().opacity == 0.0


def test_broken_json_uses_defaults(tmp_path):
    (tmp_path / "site.json").write_text("{ nao e json", encoding="utf-8")
    assert SiteConfigService(config_path=tmp_path / "site.json", app_root=tmp_path).preview_max_side() == 400


def test_non_object_json_uses_defaults(tmp_path):
    assert service(tmp_path, ["lista"]).watermark().text == "UNIARTES"
