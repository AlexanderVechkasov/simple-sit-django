"""Страницы обратной связи."""

import hashlib

from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.vary import vary_on_headers

from .forms import FeedbackForm

# Ограничение частоты: не больше 3 сообщений за 10 минут с одного адреса.
RATE_LIMIT = 3
RATE_WINDOW = 10 * 60  # в секундах


def rate_limit_key(request):
    """Ключ счётчика для этого посетителя.

    IP-адрес не храним как есть — только его «отпечаток» (хеш),
    и только в памяти на 10 минут.
    """
    # ВАЖНО для сервера: если сайт будет стоять за nginx, здесь окажется
    # адрес самого nginx.
    ip = request.META.get("REMOTE_ADDR", "")
    digest = hashlib.sha256(ip.encode()).hexdigest()[:32]
    return f"feedback:sent:{digest}"


def too_many_messages(request):
    return cache.get(rate_limit_key(request), 0) >= RATE_LIMIT


def count_message(request):
    key = rate_limit_key(request)
    cache.add(key, 0, RATE_WINDOW)  # создаёт счётчик на 10 минут, если его ещё нет
    cache.incr(key)  # +1 к счётчику


def is_from_dialog(request):
    """Запрос пришёл из окна «Написать нам» (наш JS ставит этот заголовок)."""
    return request.headers.get("X-Requested-With") == "fetch"


@require_http_methods(["GET", "POST"])
@vary_on_headers("X-Requested-With")
def feedback(request):
    """Форма обратной связи.

    Обычный переход по ссылке — целая страница /feedback/.
    Запрос из окна — только кусок HTML: сама форма или «Спасибо».
    """
    from_dialog = is_from_dialog(request)

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if too_many_messages(request):
            form.add_error(
                None,
                "Вы отправили несколько сообщений подряд. "
                "Пожалуйста, попробуйте снова минут через десять.",
            )
        elif form.is_valid():
            if not form.is_spam():
                form.save()  # сообщение сохраняется в базу
            # Боту отвечаем так же, как человеку, — пусть не догадается,
            # что его раскусили. Но в базу его сообщение не попадает.
            count_message(request)
            if from_dialog:
                return render(request, "feedback/success.html")
            # После успешной отправки — переадресация на «Спасибо».
            # Так обновление страницы не отправит сообщение второй раз.
            return redirect("feedback:thanks")
    else:
        form = FeedbackForm()

    # Первое открытие или ошибки в форме: показываем форму
    # (с ошибками и уже введённым текстом, если они есть).
    template = "feedback/form.html" if from_dialog else "feedback/feedback.html"
    return render(request, template, {"form": form})


def thanks(request):
    """Страница «Спасибо, сообщение отправлено»."""
    return render(request, "feedback/thanks.html")
