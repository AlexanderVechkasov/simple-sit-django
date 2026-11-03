"""
Импорт событий и картинок из старого статического сайта.

Запуск (путь — папка старого сайта, где лежат js/ и img/):
    uv run python manage.py import_events ../simple-sit-main

Повторный запуск безопасен: события ищутся по ключу (например, 1914a)
и обновляются, а не создаются заново. Картинки, которые уже есть,
повторно не копируются. Адрес страницы (slug) у существующих событий
не меняется, чтобы ссылки на статьи не ломались.
"""

import re
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from timeline.legacy import load_events
from timeline.models import Event, EventImage
from timeline.slugs import make_slug


class Command(BaseCommand):
    help = "Импортировать события и картинки из js/data.js старого сайта."

    def add_arguments(self, parser):
        parser.add_argument(
            "source",
            type=Path,
            help="Папка старого сайта, в которой лежат js/data.js и img/.",
        )

    def handle(self, *args, **options):
        source = options["source"].expanduser().resolve()
        data_file = source / "js" / "data.js"
        if not data_file.is_file():
            raise CommandError(f"Не найден файл {data_file}")

        items = load_events(source)
        if not items:
            raise CommandError("В data.js не найдено ни одного события.")

        created = updated = images_added = 0
        missing_images = []

        # Всё в одной транзакции: если на каком-то событии ошибка,
        # в базе не останется «половины» импорта.
        with transaction.atomic():
            for position, item in enumerate(items, start=1):
                event, is_new = self.save_event(item, order=position * 10)
                if is_new:
                    created += 1
                else:
                    updated += 1

                for number, image in enumerate(item["images"], start=1):
                    result = self.save_image(event, image, number, source)
                    if result == "added":
                        images_added += 1
                    elif result == "missing":
                        missing_images.append(image["path"])

        for path in missing_images:
            self.stdout.write(self.style.WARNING(f"Картинка не найдена: {path}"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Событий создано: {created}, обновлено: {updated}. "
                f"Картинок добавлено: {images_added}."
            )
        )

    def save_event(self, item, order):
        """Создать событие или обновить существующее с тем же ключом."""
        event = Event.objects.filter(key=item["key"]).first()
        is_new = event is None
        if is_new:
            event = Event(key=item["key"], slug=self.unique_slug(item))

        event.start_year = item["start_year"]
        event.end_year = item["end_year"]
        event.title = item["title"]
        event.summary = item["summary"]
        event.region = item["region"]
        event.outcome = item["outcome"]
        # Убираем лишние пустые строки и отступы, оставшиеся от вёрстки data.js.
        event.body = re.sub(r"\s*\n\s*", "\n", item["body"])
        event.order = order

        # Та же проверка полей, что и в админке: длина, формат адреса, годы.
        try:
            event.full_clean()
        except ValidationError as error:
            raise CommandError(f"Событие {item['key']}: {error}") from error
        event.save()  # здесь же сработает очистка HTML (метод save в модели)
        return event, is_new

    def unique_slug(self, item):
        """Адрес вида 1914-pervaya-mirovaya-voyna; при совпадении добавляем ключ."""
        slug = make_slug(item["start_year"], item["title"])
        if Event.objects.filter(slug=slug).exists():
            slug = f"{slug}-{item['key'].lower()}"
        return slug

    def save_image(self, event, image, number, source):
        """Скопировать картинку в media/events/ и привязать к событию."""
        if event.images.filter(order=number).exists():
            return "exists"  # уже импортирована раньше — не дублируем

        path = (source / image["path"]).resolve()
        # Защита: путь из data.js не должен «выходить» из папки старого сайта.
        if not path.is_relative_to(source) or not path.is_file():
            return "missing"

        # Простое имя файла вместо placeholder_1733—1735_1.jpg: 1733-1.jpg
        new_name = f"{event.key}-{number}{path.suffix.lower()}"
        with path.open("rb") as file:
            EventImage.objects.create(
                event=event,
                image=File(file, name=new_name),
                caption=image["caption"][:255],
                order=number,
            )
        return "added"
