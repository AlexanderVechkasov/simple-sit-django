"""
Очистка HTML перед сохранением в базу.

Оставляем только безопасные теги из «белого списка». Всё остальное
(<script>, <iframe>, обработчики вроде onclick, ссылки javascript:)
удаляется, чтобы чужой код не выполнился в браузере посетителя.
"""

import nh3

# Теги, которые можно использовать в тексте статьи.
# Картинок здесь нет специально: они хранятся отдельно, в EventImage.
ALLOWED_TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "ul",
    "ol",
    "li",
    "blockquote",
    "h2",
    "h3",
    "h4",
    "a",
}

# Разрешённые атрибуты: у ссылок только адрес и всплывающая подсказка.
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}

# Какие адреса можно ставить в ссылки (javascript: — нельзя).
ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


def clean_html(html: str) -> str:
    """Вернуть HTML, в котором остались только разрешённые теги и атрибуты."""
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
    ).strip()
