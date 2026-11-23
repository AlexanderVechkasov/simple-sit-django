import tempfile
from io import BytesIO, StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from feedback.models import FeedbackMessage

from .dashboard import dashboard_callback
from .images import MAX_SIDE, shrink_image
from .legacy import parse_event, parse_meta
from .login import random_login_image
from .models import Event, EventImage
from .sanitize import clean_html
from .search import search_events
from .slugs import make_slug, transliterate

User = get_user_model()


def make_image_bytes(size=(200, 100), mode="RGB", color=(120, 40, 20), fmt="PNG"):
    buffer = BytesIO()
    Image.new(mode, size, color).save(buffer, format=fmt)
    return buffer.getvalue()


class SanitizeTests(TestCase):
    def test_preserves_allowed_tags_and_links(self):
        html = (
            '<p><strong>Важно:</strong> '
            '<a href="https://example.com" title="Источник">ссылка</a></p>'
        )
        cleaned = clean_html(html)

        self.assertIn("<p>", cleaned)
        self.assertIn("<strong>Важно:</strong>", cleaned)
        self.assertIn('href="https://example.com"', cleaned)
        self.assertIn('title="Источник"', cleaned)

    def test_strips_dangerous_tags_attributes_and_schemes(self):
        dirty = (
            '<p onclick="alert(1)">Текст</p>'
            "<script>alert(1)</script>"
            '<iframe src="https://evil.example"></iframe>'
            '<img src="x" onerror="alert(1)">'
            '<a href="javascript:alert(1)">клик</a>'
        )
        cleaned = clean_html(dirty)

        self.assertIn("<p>Текст</p>", cleaned)
        self.assertNotIn("<script", cleaned)
        self.assertNotIn("<iframe", cleaned)
        self.assertNotIn("<img", cleaned)
        self.assertNotIn("onclick", cleaned)
        self.assertNotIn("javascript:", cleaned)


class SlugTests(TestCase):
    def test_transliterate_handles_case_and_special_letters(self):
        self.assertEqual(transliterate("Первая мировая война"), "Pervaya mirovaya voyna")
        self.assertEqual(transliterate("Щука и ёж 1812"), "Shchuka i ezh 1812")

    def test_make_slug_respects_max_length_without_trailing_dash(self):
        self.assertEqual(make_slug(1914, "Первая мировая война"), "1914-pervaya-mirovaya-voyna")
        short = make_slug(1812, "Отечественная война", max_length=15)
        self.assertLessEqual(len(short), 15)
        self.assertFalse(short.endswith("-"))


class ImageShrinkTests(TestCase):
    def test_small_image_is_left_untouched(self):
        data = make_image_bytes(size=(400, 300), fmt="JPEG")
        uploaded = SimpleUploadedFile("small.jpg", data, content_type="image/jpeg")

        result = shrink_image(uploaded)

        self.assertIsNone(result)
        self.assertEqual(uploaded.tell(), 0)

    def test_oversized_rgba_png_is_resized_and_converted_to_jpeg(self):
        data = make_image_bytes(
            size=(2400, 1200),
            mode="RGBA",
            color=(10, 20, 30, 0),
            fmt="PNG",
        )
        uploaded = SimpleUploadedFile("big-photo.png", data, content_type="image/png")

        result = shrink_image(uploaded)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "big-photo.jpg")
        with Image.open(result) as out:
            self.assertEqual(out.format, "JPEG")
            self.assertEqual(out.mode, "RGB")
            self.assertLessEqual(max(out.size), MAX_SIDE)
            self.assertEqual(out.size, (1920, 960))
            r, g, b = out.getpixel((0, 0))
            self.assertGreater(min(r, g, b), 240)


class LegacyParserTests(TestCase):
    def test_parse_meta_extracts_region_and_outcome(self):
        self.assertEqual(
            parse_meta("Регион: Польша | Результат: Победа"),
            ("Польша", "victory"),
        )
        self.assertEqual(
            parse_meta("Регион: Кавказ | Результат: Неопределенный"),
            ("Кавказ", "undetermined"),
        )
        self.assertEqual(parse_meta("Без разделителя"), ("", ""))

    def test_parse_event_extracts_fields_and_deduplicates_images(self):
        body = """
            yearText: '1722—1723 — Персидский поход',
            articleTitle: 'Персидский поход Петра I',
            articleMeta: 'Регион: Прикаспий | Результат: Победа',
            description: '<strong>Персидский поход (1722–1723):</strong> Поход к Каспийскому морю.',
            mainImage: 'img/1722.jpg',
            images: ['img/1722.jpg', 'img/1722-2.jpg'],
            fullContent: `<p>Начало.</p><img src="img/1722.jpg" alt="Карта похода"><p>Конец.</p>`,
        """
        parsed = parse_event("1722", body)

        self.assertEqual(parsed["start_year"], 1722)
        self.assertEqual(parsed["end_year"], 1723)
        self.assertEqual(parsed["title"], "Персидский поход Петра I")
        self.assertEqual(parsed["summary"], "Поход к Каспийскому морю.")
        self.assertEqual(parsed["region"], "Прикаспий")
        self.assertEqual(parsed["outcome"], "victory")
        self.assertNotIn("<img", parsed["body"])
        self.assertEqual(
            parsed["images"],
            [
                {"path": "img/1722.jpg", "caption": "Карта похода"},
                {"path": "img/1722-2.jpg", "caption": "Персидский поход Петра I"},
            ],
        )


class EventModelTests(TestCase):
    def test_century_and_years_display(self):
        cases = [(1701, 18), (1800, 18), (1801, 19), (1900, 19), (1901, 20)]
        for year, expected_century in cases:
            event = Event(slug=f"e-{year}", start_year=year, title="Тест", summary="Описание")
            self.assertEqual(event.century, expected_century)

        single = Event(slug="single", start_year=1794, title="Однолетнее", summary="Текст")
        same_end = Event(
            slug="same",
            start_year=1794,
            end_year=1794,
            title="Тот же год",
            summary="Текст",
        )
        span = Event(
            slug="span",
            start_year=1722,
            end_year=1723,
            title="Два года",
            summary="Текст",
        )
        self.assertEqual(single.years_display, "1794")
        self.assertEqual(same_end.years_display, "1794")
        self.assertEqual(span.years_display, "1722—1723")

    def test_save_sanitizes_body_and_strips_summary_tags(self):
        event = Event.objects.create(
            slug="1812-test",
            start_year=1812,
            title="Война 1812 года",
            summary="  <b>Краткое</b> описание  ",
            body="<p>Статья</p><script>alert(1)</script>",
        )

        self.assertEqual(event.summary, "Краткое описание")
        self.assertEqual(event.body, "<p>Статья</p>")

    def test_end_year_before_start_year_violates_constraint(self):
        with self.assertRaises(IntegrityError):
            Event.objects.create(
                slug="bad-years",
                start_year=1812,
                end_year=1810,
                title="Ошибка дат",
                summary="Описание",
            )

    def test_event_image_save_shrinks_large_upload(self):
        with tempfile.TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            event = Event.objects.create(
                slug="1812-pic",
                start_year=1812,
                title="Событие с картинкой",
                summary="Описание",
            )
            big_png = SimpleUploadedFile(
                "battle.png",
                make_image_bytes(size=(2200, 1100), fmt="PNG"),
                content_type="image/png",
            )
            img = EventImage.objects.create(event=event, image=big_png, caption="Битва")

            self.assertTrue(img.image.name.endswith(".jpg"))
            with Image.open(img.image.path) as saved:
                self.assertEqual(saved.format, "JPEG")
                self.assertLessEqual(max(saved.size), MAX_SIDE)


class TimelineViewTests(TestCase):
    def setUp(self):
        self.e1722 = Event.objects.create(
            slug="1722-persidskiy-pokhod",
            start_year=1722,
            end_year=1723,
            title="Персидский поход",
            summary="Поход Петра I.",
            order=10,
        )
        self.e1812 = Event.objects.create(
            slug="1812-otechestvennaya",
            start_year=1812,
            title="Отечественная война",
            summary="Война с Наполеоном.",
            order=10,
        )
        self.e1914 = Event.objects.create(
            slug="1914-pervaya-mirovaya",
            start_year=1914,
            end_year=1918,
            title="Первая мировая война",
            summary="Мировой конфликт.",
            order=10,
        )

    def test_index_groups_events_by_century_descending(self):
        response = self.client.get(reverse("timeline:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "timeline/index.html")
        centuries = response.context["centuries"]
        self.assertEqual([c["number"] for c in centuries], [20, 19, 18])
        self.assertEqual([c["roman"] for c in centuries], ["XX", "XIX", "XVIII"])
        self.assertEqual(response.context["first_year"], 1722)
        self.assertEqual(response.context["last_year"], 1918)

    def test_index_with_no_events(self):
        Event.objects.all().delete()
        response = self.client.get(reverse("timeline:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["centuries"], [])
        self.assertIsNone(response.context["first_year"])
        self.assertIsNone(response.context["last_year"])

    def test_event_detail_and_neighbors(self):
        response = self.client.get(self.e1812.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "timeline/event_detail.html")
        self.assertEqual(response.context["previous_event"], self.e1722)
        self.assertEqual(response.context["next_event"], self.e1914)

        first_response = self.client.get(self.e1722.get_absolute_url())
        self.assertIsNone(first_response.context["previous_event"])
        self.assertEqual(first_response.context["next_event"], self.e1812)

    def test_event_detail_404_for_missing_slug(self):
        response = self.client.get(reverse("timeline:event_detail", kwargs={"slug": "no-such"}))
        self.assertEqual(response.status_code, 404)

    def test_event_by_year_redirects_or_returns_404(self):
        response = self.client.get(reverse("timeline:event_by_year", kwargs={"year": 1812}))
        self.assertRedirects(response, self.e1812.get_absolute_url())

        missing = self.client.get(reverse("timeline:event_by_year", kwargs={"year": 1999}))
        self.assertEqual(missing.status_code, 404)


class TimelineAdminAndHelpersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="strong-password-123",
        )

    def setUp(self):
        self.e1722 = Event.objects.create(
            slug="1722-test",
            start_year=1722,
            title="Событие XVIII века",
            summary="Описание",
            outcome=Event.Outcome.VICTORY,
        )
        self.e1812 = Event.objects.create(
            slug="1812-test",
            start_year=1812,
            title="Событие XIX века",
            summary="Описание",
        )

    def test_random_login_image_returns_none_or_url(self):
        request = RequestFactory().get("/")
        self.assertIsNone(random_login_image(request))

        with tempfile.TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            upload = SimpleUploadedFile(
                "login.jpg",
                make_image_bytes(size=(200, 100), fmt="JPEG"),
                content_type="image/jpeg",
            )
            image = EventImage.objects.create(event=self.e1812, image=upload, caption="Картина")
            self.assertEqual(random_login_image(request), image.image.url)

    def test_dashboard_callback_populates_stats(self):
        FeedbackMessage.objects.create(
            email="reader@example.com",
            message="Новое непрочитанное сообщение для сводки.",
        )
        request = RequestFactory().get("/")
        context = dashboard_callback(request, {})

        stats_by_title = {card["title"]: card for card in context["stats"]}
        self.assertEqual(stats_by_title["Событий на шкале"]["value"], 2)
        self.assertIn("XVIII — 1", stats_by_title["Событий на шкале"]["note"])
        self.assertIn("XIX — 1", stats_by_title["Событий на шкале"]["note"])
        self.assertEqual(stats_by_title["Без изображения"]["value"], 2)
        self.assertEqual(stats_by_title["Непрочитанных сообщений"]["value"], 1)
        self.assertEqual(len(context["latest_messages"]["rows"]), 1)

    def test_admin_index_and_changelist_filters(self):
        self.client.force_login(self.superuser)

        index_response = self.client.get(reverse("admin:index"))
        self.assertEqual(index_response.status_code, 200)
        self.assertIn("stats", index_response.context)

        changelist_url = reverse("admin:timeline_event_changelist")
        with tempfile.TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            upload = SimpleUploadedFile(
                "pic.jpg",
                make_image_bytes(size=(200, 100), fmt="JPEG"),
                content_type="image/jpeg",
            )
            EventImage.objects.create(event=self.e1812, image=upload, caption="Фото")

            century_response = self.client.get(changelist_url, {"century": "19"})
            self.assertEqual(century_response.status_code, 200)
            self.assertContains(century_response, self.e1812.title)
            self.assertNotContains(century_response, self.e1722.title)

            with_img = self.client.get(changelist_url, {"has_image": "yes"})
            self.assertContains(with_img, self.e1812.title)
            self.assertNotContains(with_img, self.e1722.title)

            without_img = self.client.get(changelist_url, {"has_image": "no"})
            self.assertContains(without_img, self.e1722.title)
            self.assertNotContains(without_img, self.e1812.title)

    def test_admin_changelist_search_handles_cyrillic_and_key(self):
        self.e1722.key = "1722a"
        self.e1722.save(update_fields=["key"])

        self.client.force_login(self.superuser)
        changelist_url = reverse("admin:timeline_event_changelist")

        by_title = self.client.get(changelist_url, {"q": "событие xix"})
        self.assertContains(by_title, self.e1812.title)
        self.assertNotContains(by_title, self.e1722.title)

        by_key = self.client.get(changelist_url, {"q": "1722a"})
        self.assertContains(by_key, self.e1722.title)
        self.assertNotContains(by_key, self.e1812.title)


class ImportEventsCommandTests(TestCase):
    def test_import_creates_updates_and_blocks_path_traversal(self):
        with (
            tempfile.TemporaryDirectory() as site_dir,
            tempfile.TemporaryDirectory() as media_dir,
            override_settings(MEDIA_ROOT=media_dir),
        ):
            site_path = Path(site_dir)
            (site_path / "js").mkdir()
            (site_path / "img").mkdir()
            (site_path / "img" / "1722.jpg").write_bytes(
                make_image_bytes(size=(200, 100), fmt="JPEG")
            )
            (site_path / "js" / "data.js").write_text(
                """
                const events = {
                    '1722': {
                        yearText: '1722—1723 — Персидский поход',
                        articleTitle: 'Персидский поход',
                        articleMeta: 'Регион: Прикаспий | Результат: Победа',
                        description: '<strong>1722:</strong> Поход к Каспию.',
                        images: ['img/1722.jpg', '../../etc/passwd'],
                        fullContent: `<p>Текст</p><script>bad()</script>`,
                    },
                };
                """,
                encoding="utf-8",
            )

            out = StringIO()
            call_command("import_events", str(site_path), stdout=out)
            event = Event.objects.get(key="1722")
            original_slug = event.slug
            self.assertEqual(event.body, "<p>Текст</p>")
            self.assertEqual(event.images.count(), 1)

            call_command("import_events", str(site_path), stdout=StringIO())
            event.refresh_from_db()
            self.assertEqual(event.slug, original_slug)
            self.assertEqual(event.images.count(), 1)

    def test_import_raises_when_data_js_missing(self):
        with tempfile.TemporaryDirectory() as empty_dir, self.assertRaises(CommandError):
            call_command("import_events", empty_dir)


class EventSearchTests(TestCase):
    def setUp(self):
        self.persian = Event.objects.create(
            slug="1722-persidskiy-pokhod",
            start_year=1722,
            end_year=1723,
            title="Персидский поход Петра I",
            region="Прикаспий",
            outcome=Event.Outcome.VICTORY,
            summary="Поход русской армии под руководством Пётра I к Каспию.",
            body="<p><strong>Подробный</strong> разбор похода.</p>",
        )
        self.war_1812 = Event.objects.create(
            slug="1812-otechestvennaya",
            start_year=1812,
            title="Отечественная война",
            region="Российская империя",
            outcome=Event.Outcome.VICTORY,
            summary="Война с армией Наполеона.",
            body="<p>Упоминается также опыт походов Петра I.</p>",
        )

    def test_search_handles_cyrillic_case_and_yo_folding(self):
        self.assertEqual(search_events("отечественная"), [self.war_1812])
        self.assertEqual(search_events("ПЕТРА прикаспий"), [self.persian])
        self.assertEqual(search_events("пётра прикаспий"), [self.persian])

    def test_search_ranks_title_above_body_and_ignores_html_tags(self):
        self.assertEqual(search_events("петра"), [self.persian, self.war_1812])
        self.assertEqual(search_events("strong"), [])
        self.assertEqual(search_events("   "), [])

    def test_search_view_full_page_and_fetch_fragment(self):
        url = reverse("timeline:search")

        full = self.client.get(url, {"q": "1812"})
        self.assertEqual(full.status_code, 200)
        self.assertTemplateUsed(full, "timeline/search.html")
        self.assertContains(full, self.war_1812.title)
        self.assertNotContains(full, self.persian.title)

        fragment = self.client.get(
            url,
            {"q": "наполеона"},
            headers={"X-Requested-With": "fetch"},
        )
        self.assertEqual(fragment.status_code, 200)
        self.assertTemplateUsed(fragment, "timeline/search_results.html")
        self.assertTemplateNotUsed(fragment, "timeline/search.html")
        self.assertContains(fragment, self.war_1812.title)

        empty = self.client.get(url, {"q": "несуществующийзапрос"})
        self.assertEqual(empty.status_code, 200)
        self.assertContains(empty, "ничего не найдено")

    def test_header_contains_search_link(self):
        response = self.client.get(reverse("timeline:index"))
        self.assertContains(response, reverse("timeline:search"))

