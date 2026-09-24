import numpy as np
import pytest
from PIL import Image

from src.utils.preview_image import (
    DEFAULT_DPI,
    PreviewError,
    Watermark,
    contact_sheet,
    ink_bbox,
    make_preview,
    save_webp,
    size_cm,
)


def canvas(height, width, box=None, color=(200, 30, 30)):
    """RGBA transparente; opcionalmente com um retângulo opaco em box=(x0, y0, x1, y1)."""
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    if box:
        x0, y0, x1, y1 = box
        rgba[y0:y1, x0:x1] = (*color, 255)
    return rgba


def test_ink_bbox_ignores_transparent_margin():
    assert ink_bbox(canvas(50, 80, box=(10, 5, 60, 40))) == (10, 5, 60, 40)


def test_ink_bbox_ignores_almost_invisible_pixels():
    rgba = canvas(20, 20, box=(5, 5, 10, 10))
    rgba[0, 0] = (0, 0, 0, 4)
    assert ink_bbox(rgba) == (5, 5, 10, 10)


def test_ink_bbox_of_empty_image_is_none():
    assert ink_bbox(canvas(10, 10)) is None


def test_size_cm_at_300_dpi():
    assert size_cm(1181, 2953, 300) == (10.0, 25.0)


def test_size_cm_at_400_dpi():
    assert size_cm(1575, 787, 400) == (10.0, 5.0)


def test_size_cm_without_dpi_assumes_default():
    assert DEFAULT_DPI == 300
    assert size_cm(1181, 1181, None) == (10.0, 10.0)


def test_preview_is_cropped_and_measured_on_ink_area():
    rgba = canvas(1500, 2000, box=(300, 100, 1481, 1281))
    preview = make_preview(rgba, dpi=300)
    assert (preview.width_cm, preview.height_cm) == (10.0, 10.0)
    assert preview.image.size == (400, 400)
    assert preview.dpi_assumed is False


def test_preview_flags_assumed_dpi():
    assert make_preview(canvas(100, 100, box=(0, 0, 100, 100)), dpi=None).dpi_assumed is True


def test_preview_keeps_aspect_ratio_and_max_side():
    preview = make_preview(canvas(300, 1200, box=(0, 0, 1200, 300)), dpi=300, max_side=400)
    assert preview.image.size == (400, 100)


def test_small_art_is_not_upscaled():
    preview = make_preview(canvas(60, 40, box=(0, 0, 40, 60)), dpi=300, max_side=400)
    assert preview.image.size == (40, 60)


def test_empty_art_raises():
    with pytest.raises(PreviewError):
        make_preview(canvas(20, 20), dpi=300)


def test_watermark_changes_color_but_not_alpha():
    rgba = canvas(300, 300, box=(0, 0, 300, 300), color=(255, 255, 255))
    plain = np.array(make_preview(rgba, dpi=300).image)
    marked = np.array(make_preview(rgba, dpi=300, watermark=Watermark(text="UNIARTES", opacity=0.4)).image)
    assert (plain[..., :3] != marked[..., :3]).any()
    assert (plain[..., 3] == marked[..., 3]).all()


def test_watermark_does_not_appear_on_transparent_area():
    rgba = canvas(300, 300, box=(0, 0, 300, 300))
    rgba[:, 100:200] = 0  # buraco transparente no meio
    marked = np.array(make_preview(rgba, dpi=300, watermark=Watermark(text="UNIARTES", opacity=0.5)).image)
    assert (marked[:, 100:200, 3] == 0).all()
    assert (marked[:, :100, 3] == 255).all()


def test_zero_opacity_watermark_is_invisible():
    rgba = canvas(200, 200, box=(0, 0, 200, 200))
    plain = np.array(make_preview(rgba, dpi=300).image)
    marked = np.array(make_preview(rgba, dpi=300, watermark=Watermark(text="X", opacity=0)).image)
    assert (plain == marked).all()


def test_contact_sheet_fits_limit_and_keeps_pieces():
    images = [Image.new("RGBA", (200, 300), (255, 0, 0, 255)) for _ in range(5)]
    sheet = contact_sheet(images, max_side=400)
    assert max(sheet.size) <= 400
    assert np.array(sheet)[..., 3].max() == 255


def test_contact_sheet_of_one_image():
    sheet = contact_sheet([Image.new("RGBA", (50, 80), (0, 0, 0, 255))], max_side=400)
    assert sheet.size == (50, 80)


def test_save_webp_keeps_alpha(tmp_path):
    rgba = canvas(100, 100, box=(20, 20, 80, 80))
    rgba[40:50, 40:50] = 0  # furo transparente
    preview = make_preview(rgba, dpi=300)
    path = tmp_path / "sub" / "a.webp"
    save_webp(preview.image, path)
    with Image.open(path) as saved:
        assert saved.format == "WEBP"
        assert saved.mode == "RGBA"
        assert saved.size == preview.image.size
