"""
Чтение данных старого сайта (js/data.js) без Django.

Здесь только разбор текста: из файла data.js получаем список словарей
с готовыми полями для модели Event. Сохранением в базу занимается
команда import_events.
"""

import re
from pathlib import Path

EVENT_RE = re.compile(r"'(?P<key>[^']+)':\s*\{(?P<body>.*?)\n\s*\},", re.DOTALL)
STRING_FIELD_RE = re.compile(r"(?P<name>\w+):\s*'(?P<value>[^']*)'")
TEMPLATE_FIELD_RE = re.compile(r"(?P<name>\w+):\s*`(?P<value>.*?)`", re.DOTALL)
IMAGES_RE = re.compile(r"images:\s*\[(?P<items>[^\]]*)\]")
YEARS_RE = re.compile(r"(?P<start>\d{4})(?:\s*[—–-]\s*(?P<end>\d{4}))?")
IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r'(?P<name>[\w-]+)="(?P<value>[^"]*)"')
SUMMARY_PREFIX_RE = re.compile(r"^\s*<strong>.*?</strong>\s*", re.DOTALL)

OUTCOMES = {
    "победа": "victory",
    "поражение": "defeat",
    "ничья": "draw",
    "неопределённый": "undetermined",
    "неопределенный": "undetermined",
}


def parse_meta(meta: str) -> tuple[str, str]:
    """«Регион: Польша | Результат: Победа» → ("Польша", "victory")."""
    region, outcome = "", ""
    for part in meta.split("|"):
        name, _, value = part.partition(":")
        name, value = name.strip().lower(), value.strip()
        if name == "регион":
            region = value
        elif name == "результат":
            outcome = OUTCOMES.get(value.lower(), "")
    return region, outcome


def parse_event(key: str, body: str) -> dict:
    """Превратить текст одного события из data.js в словарь полей."""
    fields = {m["name"]: m["value"] for m in STRING_FIELD_RE.finditer(body)}
    fields |= {m["name"]: m["value"] for m in TEMPLATE_FIELD_RE.finditer(body)}

    years = YEARS_RE.search(fields["yearText"])
    start_year = int(years["start"])
    end_year = int(years["end"]) if years["end"] else None

    region, outcome = parse_meta(fields.get("articleMeta", ""))
    full_content = fields.get("fullContent", "")

    # Выносим <img> из HTML-текста: в Django изображения хранятся отдельно в EventImage.
    captions = {}
    for tag in IMG_TAG_RE.findall(full_content):
        attrs = {m["name"]: m["value"] for m in ATTR_RE.finditer(tag)}
        if attrs.get("src"):
            captions[attrs["src"]] = attrs.get("alt") or attrs.get("title", "")
    body_html = IMG_TAG_RE.sub("", full_content)

    paths = []
    images_match = IMAGES_RE.search(body)
    if images_match:
        paths += re.findall(r"'([^']+)'", images_match["items"])
    paths += [fields.get("mainImage", "")] + list(captions)
    paths = list(dict.fromkeys(p for p in paths if p))

    title = fields.get("articleTitle") or fields["yearText"].split(" — ", 1)[-1]

    return {
        "key": key,
        "start_year": start_year,
        "end_year": end_year if end_year != start_year else None,
        "title": title.strip(),
        "summary": SUMMARY_PREFIX_RE.sub("", fields.get("description", "")).strip(),
        "region": region,
        "outcome": outcome,
        "body": body_html.strip(),
        "images": [{"path": p, "caption": captions.get(p) or title} for p in paths],
    }


def load_events(site_dir: Path) -> list[dict]:
    """Прочитать js/data.js из папки старого сайта и вернуть список событий."""
    text = (site_dir / "js" / "data.js").read_text(encoding="utf-8")
    return [parse_event(m["key"], m["body"]) for m in EVENT_RE.finditer(text)]
