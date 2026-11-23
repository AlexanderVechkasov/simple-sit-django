"""Поиск исторических событий с учётом кириллицы и буквы ё."""

from django.utils.html import strip_tags

from .models import Event


def normalize_text(text: str) -> str:
    """Привести строку к нижнему регистру и унифицировать ё → е."""
    return text.casefold().replace("ё", "е")


def _event_fields(event: Event, *, include_internal: bool = False) -> tuple[str, str]:
    primary = normalize_text(
        f"{event.years_display} {event.start_year} {event.end_year or ''} {event.title}"
    )
    parts = [
        event.region,
        event.get_outcome_display(),
        event.summary,
        strip_tags(event.body),
    ]
    if include_internal:
        parts.extend([event.key or "", event.slug])
    return primary, normalize_text(" ".join(parts))


def search_events(query: str, queryset=None, *, include_internal: bool = False) -> list[Event]:
    """Найти события, содержащие все слова запроса (без учёта регистра и ё/е).

    Совпадения в годах и заголовке поднимаются выше совпадений только в описании.
    """
    tokens = normalize_text(query).split()
    if not tokens:
        return []

    events = queryset if queryset is not None else Event.objects.all()
    primary_matches = []
    secondary_matches = []

    for event in events:
        primary, secondary = _event_fields(event, include_internal=include_internal)
        combined = f"{primary} {secondary}"
        if not all(token in combined for token in tokens):
            continue
        if all(token in primary for token in tokens):
            primary_matches.append(event)
        else:
            secondary_matches.append(event)

    return primary_matches + secondary_matches
