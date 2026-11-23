"""Уменьшение картинок при загрузке (вызывается из EventImage.save)."""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_SIDE = 1920
MAX_BYTES = 1024 * 1024
JPEG_QUALITY = 85


def to_rgb(img):
    """Конвертировать изображение в RGB, заливая прозрачность белым для JPEG."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, "white")
        background.paste(img, mask=img.getchannel("A"))
        return background
    return img.convert("RGB")


def shrink_image(image_file):
    """Уменьшить и пересохранить изображение в JPEG, если оно превышает лимиты.

    Возвращает None, если файл уже вписывается в MAX_SIDE и MAX_BYTES.
    """
    image_file.seek(0)
    with Image.open(image_file) as img:
        if max(img.size) <= MAX_SIDE and image_file.size <= MAX_BYTES:
            image_file.seek(0)
            return None

        # Учитываем ориентацию из EXIF, чтобы фото с телефонов не сохранялись повёрнутыми.
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        img = to_rgb(img)

        buffer = BytesIO()
        img.save(buffer, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)

    name = Path(image_file.name).with_suffix(".jpg").name
    return ContentFile(buffer.getvalue(), name=name)
