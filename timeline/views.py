"""Страницы исторической шкалы."""

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET
from django.views.decorators.vary import vary_on_headers

from .models import Event
from .search import search_events

ROMAN_CENTURIES = {17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX", 21: "XXI"}


def timeline(request):
    """Главная страница: события, сгруппированные по векам."""
    events = list(Event.objects.prefetch_related("images"))

    by_century = {}
    for event in events:
        by_century.setdefault(event.century, []).append(event)

    centuries = [
        {
            "number": number,
            "roman": ROMAN_CENTURIES.get(number, str(number)),
            "events": by_century[number],
        }
        for number in sorted(by_century, reverse=True)
    ]

    context = {
        "centuries": centuries,
        "first_year": min((e.start_year for e in events), default=None),
        "last_year": max((e.end_year or e.start_year for e in events), default=None),
    }
    return render(request, "timeline/index.html", context)


def event_detail(request, slug):
    """Страница статьи одного события."""
    event = get_object_or_404(Event.objects.prefetch_related("images"), slug=slug)

    all_events = list(
        Event.objects.order_by("start_year", "order", "pk").only(
            "slug", "title", "start_year", "end_year"
        )
    )
    position = next(i for i, item in enumerate(all_events) if item.pk == event.pk)
    previous_event = all_events[position - 1] if position > 0 else None
    next_event = all_events[position + 1] if position + 1 < len(all_events) else None

    context = {
        "event": event,
        "previous_event": previous_event,
        "next_event": next_event,
    }
    return render(request, "timeline/event_detail.html", context)


def event_by_year(request, year):
    """Перенаправить короткий адрес /events/<year>/ на первое событие этого года."""
    event = Event.objects.filter(start_year=year).first()
    if event is None:
        raise Http404("В этом году событий нет.")
    return redirect(event)


@require_GET
@vary_on_headers("X-Requested-With")
def search(request):
    """Поиск событий (полная страница /search/ или HTML-фрагмент для модального окна)."""
    query = request.GET.get("q", "").strip()
    results = search_events(query) if query else []
    context = {"query": query, "results": results}

    if request.headers.get("X-Requested-With") == "fetch":
        return render(request, "timeline/search_results.html", context)
    return render(request, "timeline/search.html", context)
