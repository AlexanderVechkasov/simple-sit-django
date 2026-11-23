"""Страницы обратной связи."""

import hashlib

from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.vary import vary_on_headers

from .forms import FeedbackForm

RATE_LIMIT = 3
RATE_WINDOW = 10 * 60


def rate_limit_key(request):
    """Вернуть хеш IP посетителя для временного счётчика rate-limit."""
    # TODO: на сервере за обратным прокси нужно учитывать X-Forwarded-For.
    ip = request.META.get("REMOTE_ADDR", "")
    digest = hashlib.sha256(ip.encode()).hexdigest()[:32]
    return f"feedback:sent:{digest}"


def too_many_messages(request):
    return cache.get(rate_limit_key(request), 0) >= RATE_LIMIT


def count_message(request):
    key = rate_limit_key(request)
    cache.add(key, 0, RATE_WINDOW)
    cache.incr(key)


def is_from_dialog(request):
    """Проверить, что запрос отправлен из модального окна через fetch."""
    return request.headers.get("X-Requested-With") == "fetch"


@require_http_methods(["GET", "POST"])
@vary_on_headers("X-Requested-With")
def feedback(request):
    """Обработать форму обратной связи (полная страница или фрагмент для диалога)."""
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
                form.save()
            # Спам-боту возвращаем обычный успешный ответ, не раскрывая срабатывание honeypot.
            count_message(request)
            if from_dialog:
                return render(request, "feedback/success.html")
            return redirect("feedback:thanks")
    else:
        form = FeedbackForm()

    template = "feedback/form.html" if from_dialog else "feedback/feedback.html"
    return render(request, template, {"form": form})


def thanks(request):
    """Страница «Спасибо, сообщение отправлено»."""
    return render(request, "feedback/thanks.html")
