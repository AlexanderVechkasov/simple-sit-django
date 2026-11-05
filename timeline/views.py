"""Страницы исторической шкалы."""

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from .models import Event

def timeline(request):
    """Главная страница: все события на вертикальной шкале."""
    events = Event.objects.prefetch_related("images")
    return render(request, "timeline/index.html", {"events": events})


def event_detail(request, slug):
    """Страница-статья одного события: /events/1914-pervaya-mirovaya-voyna/."""
    event = get_object_or_404(Event.objects.prefetch_related("images"), slug=slug)
    return render(request, "timeline/event_detail.html", {"event": event})


def event_by_year(request, year):
    """Короткий адрес /events/1914/ ведёт на полный адрес статьи.
    Если в этом году несколько событий (например, 1735), ведём на первое
    по порядку шкалы. Если событий нет — страница «не найдено».
    """
    event = Event.objects.filter(start_year=year).first()
    if event is None:
        raise Http404("В этом году событий нет.")
    # redirect() сам возьмёт адрес из event.get_absolute_url().
    return redirect(event)
