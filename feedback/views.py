"""Страницы обратной связи."""

from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from .forms import FeedbackForm

@require_http_methods(["GET", "POST"])
def feedback(request):
    """Страница с формой. GET — показать форму, POST — принять сообщение."""
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()  # сообщение сохраняется в базу
            # После успешной отправки — переадресация на «Спасибо».
            # Так обновление страницы не отправит сообщение второй раз.
            return redirect("feedback:thanks")
    else:
        form = FeedbackForm()

    # Сюда попадаем при первом открытии или если в форме ошибки:
    # тогда форма покажется снова, с ошибками и уже введённым текстом.
    return render(request, "feedback/feedback.html", {"form": form})


def thanks(request):
    """Страница «Спасибо, сообщение отправлено»."""
    return render(request, "feedback/thanks.html")
