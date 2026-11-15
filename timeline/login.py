"""Картинка для страницы входа в админку (подключена в UNFOLD["LOGIN"]["image"])."""

from .models import EventImage


def random_login_image(request):
    """Случайная картина из событий шкалы — при каждом открытии страницы входа своя.

    Возвращает адрес картинки. Если картинок пока нет — None,
    и Unfold просто не покажет правую половину.
    """
    image = EventImage.objects.order_by("?").first()
    return image.image.url if image else None
