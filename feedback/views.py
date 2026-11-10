"""Страницы обратной связи."""

from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.vary import vary_on_headers
from .forms import FeedbackForm

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
        if form.is_valid():
            form.save()  # сообщение сохраняется в базу
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
