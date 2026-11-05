"""Страницы исторической шкалы."""

from django.shortcuts import render
from .models import Event

def timeline(request):
    """Главная страница: все события на вертикальной шкале."""

    events = Event.objects.prefetch_related("images")
    return render(request, "timeline/index.html", {"events": events})
