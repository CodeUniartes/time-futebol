from dataclasses import dataclass

import numpy as np
import tifffile

CM_PER_INCH = 2.54


class TiffReadError(Exception):
    pass


@dataclass
class TiffImage:
    rgba: np.ndarray
    dpi: float = None


def read_tiff(path):
    try:
        with tifffile.TiffFile(path) as tiff:
            page = tiff.pages[0]
            photometric = page.photometric.name
            extrasamples = [sample.name for sample in page.extrasamples]
            data = page.asarray()
            dpi = _dpi(page)
    except Exception as error:
        raise TiffReadError(f"Não foi possível ler o TIFF: {error}") from error

    try:
        rgba = _to_rgba(_to_uint8(data), photometric, extrasamples)
    except TiffReadError:
        raise
    except Exception as error:
        raise TiffReadError(f"TIFF em formato não suportado: {error}") from error
    return TiffImage(rgba=rgba, dpi=dpi)


def _to_uint8(data):
    if data.dtype == np.uint8:
        return data
    if data.dtype == np.uint16:
        return (data >> 8).astype(np.uint8)
    raise TiffReadError(f"TIFF com profundidade {data.dtype} não suportada.")


def _to_rgba(data, photometric, extrasamples):
    if data.ndim == 2:
        if photometric not in ("MINISBLACK", "MINISWHITE"):
            raise TiffReadError(f"TIFF com modo {photometric} não suportado.")
        gray = 255 - data if photometric == "MINISWHITE" else data
        alpha = np.full(data.shape, 255, dtype=np.uint8)
        return np.dstack([gray, gray, gray, alpha])

    if photometric == "SEPARATED":
        if data.shape[2] < 4:
            raise TiffReadError("TIFF CMYK com menos de 4 canais.")
        color = _cmyk_to_rgb(data[..., :4])
        base = 4
    elif photometric == "RGB":
        color = data[..., :3]
        base = 3
    else:
        raise TiffReadError(f"TIFF com modo {photometric} não suportado.")

    alpha = np.full(data.shape[:2], 255, dtype=np.uint8)
    for offset, name in enumerate(extrasamples):
        if "ALPHA" not in name or base + offset >= data.shape[2]:
            continue
        alpha = data[..., base + offset]
        if name == "ASSOCALPHA":
            color = _unpremultiply(color, alpha)
        break
    return np.dstack([color, alpha])


def _cmyk_to_rgb(cmyk):
    # No TIFF do Photoshop, 255 é tinta cheia.
    channels = cmyk.astype(np.uint16)
    k = 255 - channels[..., 3]
    rgb = [(255 - channels[..., index]) * k // 255 for index in range(3)]
    return np.stack(rgb, axis=-1).astype(np.uint8)


def _unpremultiply(color, alpha):
    divisor = np.maximum(alpha.astype(np.uint16), 1)[..., None]
    restored = np.minimum(color.astype(np.uint16) * 255 // divisor, 255)
    return np.where(alpha[..., None] > 0, restored, 0).astype(np.uint8)


def _dpi(page):
    resolution = page.tags.get("XResolution")
    if resolution is None:
        return None
    numerator, denominator = resolution.value
    if not denominator:
        return None
    value = numerator / denominator
    unit = page.tags.get("ResolutionUnit")
    unit_name = unit.value.name if unit is not None else "INCH"
    if unit_name == "INCH":
        return value
    if unit_name == "CENTIMETER":
        return value * CM_PER_INCH
    return None
