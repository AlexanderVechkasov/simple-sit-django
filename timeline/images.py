"""Уменьшение картинок при загрузке (вызывается из EventImage.save)."""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

# Больше этого по длинной стороне сайту не нужно: в статье картинка ~720 px,
# в увеличенном просмотре галереи — не больше экрана.
MAX_SIDE = 1920
# Картинки не больше MAX_SIDE и легче этого оставляем как есть — без пересжатия.
MAX_BYTES = 1024 * 1024  # 1 МБ
JPEG_QUALITY = 85  # 85 из 100: на глаз как оригинал, а файл в разы меньше


def to_rgb(img):
    """JPEG не умеет прозрачность: прозрачные места заливаем белым."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, "white")
        background.paste(img, mask=img.getchannel("A"))
        return background
    return img.convert("RGB")


def shrink_image(image_file):
    """Вернуть уменьшенную копию картинки в JPEG.

    Если картинка и так небольшая и лёгкая, возвращает None —
    тогда сохраняем оригинал без изменений.
    """
    image_file.seek(0)
    with Image.open(image_file) as img:
        if max(img.size) <= MAX_SIDE and image_file.size <= MAX_BYTES:
            image_file.seek(0)
            return None

        # Фото с телефона бывают «лёжа» с пометкой о повороте — поворачиваем как надо.
        img = ImageOps.exif_transpose(img)
        # thumbnail только уменьшает и сохраняет пропорции.
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        img = to_rgb(img)

        buffer = BytesIO()
        img.save(buffer, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)

    # Имя то же, но с расширением .jpg: «Снимок экрана.png» → «Снимок экрана.jpg».
    name = Path(image_file.name).with_suffix(".jpg").name
    return ContentFile(buffer.getvalue(), name=name)
