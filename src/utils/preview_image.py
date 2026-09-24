import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CM_PER_INCH = 2.54
DEFAULT_DPI = 300
ALPHA_THRESHOLD = 8
PREVIEW_MAX_SIDE = 400
WEBP_QUALITY = 80
WATERMARK_COLOR = (110, 110, 110)


class PreviewError(Exception):
    pass


@dataclass
class Watermark:
    text: str = "UNIARTES"
    opacity: float = 0.25
    angle: float = 30.0


@dataclass
class Preview:
    image: Image.Image
    width_cm: float
    height_cm: float
    dpi_assumed: bool


def ink_bbox(rgba, threshold=ALPHA_THRESHOLD):
    """Retângulo (x0, y0, x1, y1) que contém todo pixel com alfa acima do limiar; None se não houver."""
    visible = rgba[..., 3] > threshold
    rows = np.flatnonzero(visible.any(axis=1))
    columns = np.flatnonzero(visible.any(axis=0))
    if rows.size == 0 or columns.size == 0:
        return None
    return int(columns[0]), int(rows[0]), int(columns[-1]) + 1, int(rows[-1]) + 1


def size_cm(width_px, height_px, dpi):
    dpi = dpi or DEFAULT_DPI
    return round(width_px / dpi * CM_PER_INCH, 1), round(height_px / dpi * CM_PER_INCH, 1)


def make_preview(rgba, dpi, max_side=PREVIEW_MAX_SIDE, watermark=None):
    box = ink_bbox(rgba)
    if box is None:
        raise PreviewError("A arte não tem nenhum pixel visível.")
    x0, y0, x1, y1 = box
    cropped = rgba[y0:y1, x0:x1]
    width_cm, height_cm = size_cm(x1 - x0, y1 - y0, dpi)

    image = Image.fromarray(cropped, "RGBA")
    scale = min(1.0, max_side / max(image.size))
    if scale < 1.0:
        new_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
        image = image.resize(new_size, Image.LANCZOS)
    if watermark is not None and watermark.text and watermark.opacity > 0:
        image = apply_watermark(image, watermark)
    return Preview(image=image, width_cm=width_cm, height_cm=height_cm, dpi_assumed=not dpi)


def apply_watermark(image, watermark):
    """Texto repetido na diagonal por cima da arte; o alfa da arte não muda."""
    layer = _watermark_layer(image.size, watermark)
    pixels = np.array(image, dtype=np.float32)
    strength = (layer.astype(np.float32) / 255.0)[..., None] * float(watermark.opacity)
    color = np.array(WATERMARK_COLOR, dtype=np.float32)
    pixels[..., :3] = pixels[..., :3] * (1.0 - strength) + color * strength
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), "RGBA")


def _watermark_layer(size, watermark):
    width, height = size
    diagonal = math.ceil(math.hypot(width, height))
    font_size = max(10, round(min(width, height) / 6))
    font = ImageFont.load_default(size=font_size)
    step_x = max(font_size * 6, 1)
    step_y = max(round(font_size * 2.2), 1)

    canvas = Image.new("L", (diagonal * 2, diagonal * 2), 0)
    draw = ImageDraw.Draw(canvas)
    for row, y in enumerate(range(0, diagonal * 2, step_y)):
        offset = (row % 2) * (step_x // 2)
        for x in range(-step_x, diagonal * 2, step_x):
            draw.text((x + offset, y), watermark.text, fill=255, font=font)
    rotated = canvas.rotate(watermark.angle, resample=Image.BICUBIC)
    left = (rotated.width - width) // 2
    top = (rotated.height - height) // 2
    return np.array(rotated.crop((left, top, left + width, top + height)))


def contact_sheet(images, max_side=PREVIEW_MAX_SIDE):
    """Colagem em grade das imagens, com no máximo max_side no lado maior."""
    if len(images) == 1:
        return images[0].copy()
    columns = math.ceil(math.sqrt(len(images)))
    rows = math.ceil(len(images) / columns)
    cell_width = max(image.width for image in images)
    cell_height = max(image.height for image in images)
    sheet = Image.new("RGBA", (cell_width * columns, cell_height * rows), (0, 0, 0, 0))
    for index, image in enumerate(images):
        column, row = index % columns, index // columns
        left = column * cell_width + (cell_width - image.width) // 2
        top = row * cell_height + (cell_height - image.height) // 2
        sheet.paste(image, (left, top), image)
    scale = min(1.0, max_side / max(sheet.size))
    if scale < 1.0:
        sheet = sheet.resize((max(1, round(sheet.width * scale)), max(1, round(sheet.height * scale))), Image.LANCZOS)
    return sheet


def save_webp(image, path, quality=WEBP_QUALITY):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "WEBP", quality=quality)
