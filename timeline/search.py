"""Поиск исторических событий с учётом кириллицы и буквы ё."""

from django.utils.html import strip_tags

from .models import Event


def normalize_text(text: str) -> str:
    """Привести строку к нижнему регистру и унифицировать ё → е."""
    return text.casefold().replace("ё", "е")


def _event_searchable_text(event: Event, *, include_internal: bool = False) -> str:
    parts = [
        event.years_display,
        str(event.start_year),
        str(event.end_year or ""),
        event.title,
        event.region,
        event.get_outcome_display(),
        event.summary,
        strip_tags(event.body),
    ]
    if include_internal:
        parts.extend([event.key or "", event.slug])
    return normalize_text(" ".join(parts))


def search_events(query: str, queryset=None, *, include_internal: bool = False) -> list[Event]:
    """Найти события по всем словам запроса (без учёта регистра и ё/е).

    Сохраняет порядок шкалы: от более поздних лет к более ранним.
    """
    tokens = normalize_text(query).split()
    if not tokens:
        return []

    events = queryset if queryset is not None else Event.objects.all()
    results = []
    for event in events:
        text = _event_searchable_text(event, include_internal=include_internal)
        if all(token in text for token in tokens):
            results.append(event)
    return results
