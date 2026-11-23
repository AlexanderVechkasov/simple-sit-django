"""Красивые адреса: перевод русского текста в латиницу."""

from django.utils.text import slugify

TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def transliterate(text: str) -> str:
    """«Первая мировая война» → «Pervaya mirovaya voyna»."""
    result = []
    for char in text:
        latin = TRANSLIT.get(char.lower())
        if latin is None:
            result.append(char)
        elif char.isupper():
            result.append(latin.capitalize())
        else:
            result.append(latin)
    return "".join(result)


def make_slug(start_year: int, title: str, max_length: int = 150) -> str:
    """Адрес события: «1914-pervaya-mirovaya-voyna»."""
    slug = slugify(f"{start_year} {transliterate(title)}")
    return slug[:max_length].rstrip("-")
