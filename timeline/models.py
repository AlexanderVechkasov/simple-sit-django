"""Модели исторической шкалы: события и их изображения."""

from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags

from .sanitize import clean_html


class Event(models.Model):
    """Историческое событие на шкале."""

    class Outcome(models.TextChoices):
        # Слева — что хранится в базе, справа — что видит человек.
        VICTORY = "victory", "Победа"
        DEFEAT = "defeat", "Поражение"
        DRAW = "draw", "Ничья"
        UNDETERMINED = "undetermined", "Неопределённый"

    key = models.CharField(
        "ключ из старого сайта",
        max_length=10,
        unique=True,
        help_text=(
            "Например, 1914a или 1735b. По нему импорт находит событие и не создаёт дубликатов."
        ),
    )
    slug = models.SlugField(
        "адрес страницы",
        max_length=150,
        unique=True,
        help_text="Часть адреса статьи: /events/<адрес>/. Только латиница, цифры и дефисы.",
    )
    start_year = models.PositiveSmallIntegerField("год начала")
    end_year = models.PositiveSmallIntegerField(
        "год окончания",
        null=True,
        blank=True,
        help_text="Оставьте пустым, если событие уложилось в один год.",
    )
    title = models.CharField("заголовок", max_length=200)
    summary = models.TextField(
        "краткая справка",
        help_text="Показывается в раскрытой карточке на шкале. Обычный текст, без HTML.",
    )
    region = models.CharField("регион", max_length=255, blank=True)
    outcome = models.CharField("итог", max_length=20, choices=Outcome.choices, blank=True)
    body = models.TextField(
        "полный текст",
        blank=True,
        help_text="Текст статьи в HTML. При сохранении очищается от опасных тегов.",
    )
    order = models.PositiveIntegerField(
        "порядок",
        default=0,
        help_text="Чем меньше число, тем выше событие на шкале.",
    )
    created_at = models.DateTimeField("создано", auto_now_add=True)
    updated_at = models.DateTimeField("изменено", auto_now=True)

    class Meta:
        ordering = ["order", "start_year", "key"]
        verbose_name = "событие"
        verbose_name_plural = "события"
        constraints = [
            # Защита на уровне базы: год окончания не раньше года начала.
            models.CheckConstraint(
                condition=models.Q(end_year__isnull=True)
                | models.Q(end_year__gte=models.F("start_year")),
                name="event_end_year_after_start_year",
            ),
        ]

    def __str__(self):
        return f"{self.years_display} — {self.title}"

    def save(self, *args, **kwargs):
        # Очищаем текст при КАЖДОМ сохранении: из админки, импорта или кода.
        self.body = clean_html(self.body)
        # Краткая справка — обычный текст, поэтому теги убираем полностью.
        self.summary = strip_tags(self.summary).strip()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Адрес страницы события: /events/<slug>/."""
        return reverse("timeline:event_detail", kwargs={"slug": self.slug})

    @property
    def century(self):
        """Век по году начала: 1722 → 18, 1801 → 19, 1900 → 19."""
        return (self.start_year - 1) // 100 + 1

    @property
    def years_display(self):
        """Годы для показа: «1722—1723» или просто «1794»."""
        if self.end_year and self.end_year != self.start_year:
            return f"{self.start_year}—{self.end_year}"
        return str(self.start_year)


class EventImage(models.Model):
    """Изображение к событию. У события может быть несколько картинок."""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="событие",
    )
    image = models.ImageField("изображение", upload_to="events/")
    caption = models.CharField(
        "подпись",
        max_length=255,
        help_text=(
            "Показывается в галерее и служит альтернативным текстом (alt) "
            "для незрячих пользователей."
        ),
    )
    source = models.CharField(
        "источник",
        max_length=255,
        blank=True,
        help_text="Откуда изображение: автор, музей или ссылка.",
    )
    order = models.PositiveSmallIntegerField("порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "изображение"
        verbose_name_plural = "изображения"

    def __str__(self):
        return self.caption
