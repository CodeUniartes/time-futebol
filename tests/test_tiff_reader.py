import numpy as np
import pytest
import tifffile

from src.utils.tiff_reader import TiffReadError, read_tiff


def write(path, data, **kwargs):
    kwargs.setdefault("resolution", (300, 300))
    kwargs.setdefault("resolutionunit", "INCH")
    if data.ndim == 3:
        kwargs.setdefault("planarconfig", "contig")
    tifffile.imwrite(path, data, **kwargs)
    return path


def solid(height, width, channels, value, dtype=np.uint8):
    return np.full((height, width, channels), value, dtype=dtype)


def test_rgb_is_opaque(tmp_path):
    data = solid(4, 6, 3, 0)
    data[..., 0] = 200
    image = read_tiff(write(tmp_path / "a.tif", data, photometric="rgb"))
    assert image.rgba.shape == (4, 6, 4)
    assert tuple(image.rgba[0, 0]) == (200, 0, 0, 255)


def test_rgba_keeps_alpha(tmp_path):
    data = solid(3, 3, 4, 255)
    data[0, 0, 3] = 0
    image = read_tiff(write(tmp_path / "a.tif", data, photometric="rgb", extrasamples=["unassalpha"]))
    assert image.rgba[0, 0, 3] == 0
    assert image.rgba[1, 1, 3] == 255


def test_rgb_with_two_extra_channels_reads_alpha(tmp_path):
    data = solid(3, 3, 5, 255)
    data[0, 0, 3] = 0
    image = read_tiff(
        write(tmp_path / "a.tif", data, photometric="rgb", extrasamples=["unassalpha", "unspecified"])
    )
    assert image.rgba[0, 0, 3] == 0
    assert image.rgba[2, 2, 3] == 255


def test_cmyk_with_alpha_converts_to_rgb(tmp_path):
    data = solid(3, 3, 5, 0)
    data[..., 1] = 255  # magenta pleno
    data[..., 4] = 255  # alfa opaco
    data[0, 0, 4] = 0
    image = read_tiff(write(tmp_path / "a.tif", data, photometric="separated", extrasamples=["unassalpha"]))
    assert tuple(image.rgba[1, 1]) == (255, 0, 255, 255)
    assert image.rgba[0, 0, 3] == 0


def test_cmyk_black_and_white(tmp_path):
    data = solid(2, 2, 5, 0)
    data[..., 4] = 255
    data[0, :, 3] = 255  # K pleno na primeira linha
    image = read_tiff(write(tmp_path / "a.tif", data, photometric="separated", extrasamples=["unassalpha"]))
    assert tuple(image.rgba[0, 0][:3]) == (0, 0, 0)
    assert tuple(image.rgba[1, 0][:3]) == (255, 255, 255)


def test_cmyk_with_six_channels_uses_the_alpha_one(tmp_path):
    data = solid(3, 3, 6, 0)
    data[..., 4] = 255  # alfa
    data[0, 0, 4] = 0
    data[..., 5] = 128  # canal extra sem significado
    image = read_tiff(
        write(tmp_path / "a.tif", data, photometric="separated", extrasamples=["unassalpha", "unspecified"])
    )
    assert image.rgba[0, 0, 3] == 0
    assert image.rgba[1, 1, 3] == 255


def test_sixteen_bit_is_scaled_to_eight(tmp_path):
    data = solid(2, 2, 4, 65535, dtype=np.uint16)
    data[0, 0, 0] = 0
    image = read_tiff(write(tmp_path / "a.tif", data, photometric="rgb", extrasamples=["unassalpha"]))
    assert image.rgba.dtype == np.uint8
    assert tuple(image.rgba[0, 0]) == (0, 255, 255, 255)


def test_grayscale_is_supported(tmp_path):
    data = np.array([[0, 255], [128, 64]], dtype=np.uint8)
    image = read_tiff(write(tmp_path / "a.tif", data, photometric="minisblack"))
    assert tuple(image.rgba[0, 1]) == (255, 255, 255, 255)
    assert tuple(image.rgba[0, 0]) == (0, 0, 0, 255)


def test_lzw_compression(tmp_path):
    data = solid(20, 20, 4, 90)
    path = write(tmp_path / "a.tif", data, photometric="rgb", extrasamples=["unassalpha"], compression="lzw")
    assert read_tiff(path).rgba.shape == (20, 20, 4)


def test_dpi_in_inches(tmp_path):
    image = read_tiff(write(tmp_path / "a.tif", solid(2, 2, 3, 0), photometric="rgb", resolution=(400, 400)))
    assert image.dpi == pytest.approx(400)


def test_dpi_in_centimeters_is_converted_to_inches(tmp_path):
    path = write(
        tmp_path / "a.tif", solid(2, 2, 3, 0), photometric="rgb", resolution=(118.11, 118.11), resolutionunit="CENTIMETER"
    )
    assert read_tiff(path).dpi == pytest.approx(300, abs=0.1)


def test_missing_dpi_is_none(tmp_path):
    path = tmp_path / "a.tif"
    tifffile.imwrite(path, solid(2, 2, 3, 0), photometric="rgb", resolution=None)
    assert read_tiff(path).dpi is None


def test_unit_none_means_unknown_dpi(tmp_path):
    path = write(tmp_path / "a.tif", solid(2, 2, 3, 0), photometric="rgb", resolutionunit="NONE")
    assert read_tiff(path).dpi is None


def test_missing_file_raises_read_error(tmp_path):
    with pytest.raises(TiffReadError):
        read_tiff(tmp_path / "nao_existe.tif")


def test_corrupted_file_raises_read_error(tmp_path):
    path = tmp_path / "a.tif"
    path.write_bytes(b"isto nao e um tiff")
    with pytest.raises(TiffReadError):
        read_tiff(path)


def test_truncated_file_raises_read_error(tmp_path):
    path = write(tmp_path / "a.tif", solid(200, 200, 4, 7), photometric="rgb", extrasamples=["unassalpha"])
    path.write_bytes(path.read_bytes()[:120])
    with pytest.raises(TiffReadError):
        read_tiff(path)
