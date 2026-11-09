"""Страницы исторической шкалы."""

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from .models import Event

# Римские цифры для заголовков веков.
ROMAN_CENTURIES = {17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX", 21: "XXI"}


def timeline(request):
    """Главная страница: все события, сгруппированные по векам."""
    # prefetch_related загружает картинки всех событий одним запросом,
    # а не отдельным запросом на каждое из 60 событий.
    events = list(Event.objects.prefetch_related("images"))

    # Раскладываем события по векам: {18: [...], 19: [...], 20: [...]}
    by_century = {}
    for event in events:
        by_century.setdefault(event.century, []).append(event)

    centuries = [
        {
            "number": number,
            "roman": ROMAN_CENTURIES.get(number, str(number)),
            "events": by_century[number],
        }
        for number in sorted(by_century)
    ]

    context = {
        "centuries": centuries,
        # Границы для вступления: «1722–1918 годов»
        "first_year": min((e.start_year for e in events), default=None),
        "last_year": max((e.end_year or e.start_year for e in events), default=None),
    }
    return render(request, "timeline/index.html", context)


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
