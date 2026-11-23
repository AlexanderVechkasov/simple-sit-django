from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .admin import unread_badge
from .dashboard import latest_messages_table
from .forms import FeedbackForm
from .models import FeedbackMessage
from .views import RATE_LIMIT

User = get_user_model()


class FeedbackModelTests(TestCase):
    def test_defaults_and_str(self):
        msg = FeedbackMessage.objects.create(
            email="reader@example.com",
            message="Нашёл опечатку в статье про 1812 год.",
        )

        self.assertFalse(msg.is_read)
        expected_time = timezone.localtime(msg.created_at).strftime("%d.%m.%Y %H:%M")
        self.assertEqual(str(msg), f"reader@example.com, {expected_time}")

    def test_ordering_newest_first(self):
        older = FeedbackMessage.objects.create(
            email="first@example.com",
            message="Первое сообщение для проверки порядка.",
        )
        newer = FeedbackMessage.objects.create(
            email="second@example.com",
            message="Второе сообщение для проверки порядка.",
        )

        self.assertEqual(list(FeedbackMessage.objects.all()), [newer, older])


class FeedbackFormTests(TestCase):
    def test_valid_form_is_not_spam(self):
        form = FeedbackForm(
            data={
                "email": "user@example.com",
                "message": "Спасибо за подробную историческую шкалу!",
                "homepage": "",
            }
        )

        self.assertTrue(form.is_valid())
        self.assertFalse(form.is_spam())
        self.assertEqual(form.label_suffix, "")

    def test_short_message_rejected(self):
        form = FeedbackForm(
            data={
                "email": "user@example.com",
                "message": "   привет   ",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)

    def test_honeypot_marks_submission_as_spam(self):
        form = FeedbackForm(
            data={
                "email": "bot@example.com",
                "message": "Отличное предложение купить рекламу недорого!",
                "homepage": "https://spam.example",
            }
        )

        self.assertTrue(form.is_valid())
        self.assertTrue(form.is_spam())


class FeedbackViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.form_url = reverse("feedback:form")
        self.thanks_url = reverse("feedback:thanks")
        self.valid_data = {
            "email": "reader@example.com",
            "message": "Хороший сайт, добавьте пожалуйста ещё карт.",
            "homepage": "",
        }

    def tearDown(self):
        cache.clear()

    def test_get_full_page_and_dialog_fragment(self):
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "feedback/feedback.html")

        dialog_response = self.client.get(
            self.form_url,
            headers={"X-Requested-With": "fetch"},
        )
        self.assertEqual(dialog_response.status_code, 200)
        self.assertTemplateUsed(dialog_response, "feedback/form.html")
        self.assertTemplateNotUsed(dialog_response, "feedback/feedback.html")

    def test_post_saves_message_and_redirects_to_thanks(self):
        response = self.client.post(self.form_url, data=self.valid_data)

        self.assertRedirects(response, self.thanks_url)
        self.assertEqual(FeedbackMessage.objects.count(), 1)
        saved = FeedbackMessage.objects.get()
        self.assertEqual(saved.email, self.valid_data["email"])
        self.assertEqual(saved.message, self.valid_data["message"])

    def test_post_from_dialog_returns_success_fragment(self):
        response = self.client.post(
            self.form_url,
            data=self.valid_data,
            headers={"X-Requested-With": "fetch"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "feedback/success.html")
        self.assertEqual(FeedbackMessage.objects.count(), 1)

    def test_honeypot_spam_not_saved_but_looks_successful(self):
        spam_data = {**self.valid_data, "homepage": "http://bot.example"}

        response = self.client.post(self.form_url, data=spam_data)

        self.assertRedirects(response, self.thanks_url)
        self.assertEqual(FeedbackMessage.objects.count(), 0)

    def test_invalid_post_rerenders_form_with_errors(self):
        response = self.client.post(
            self.form_url,
            data={"email": "not-an-email", "message": "мало"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "feedback/feedback.html")
        self.assertEqual(FeedbackMessage.objects.count(), 0)

    def test_rate_limit_blocks_after_threshold(self):
        for _ in range(RATE_LIMIT):
            response = self.client.post(self.form_url, data=self.valid_data)
            self.assertRedirects(response, self.thanks_url)

        blocked = self.client.post(self.form_url, data=self.valid_data)

        self.assertEqual(blocked.status_code, 200)
        self.assertEqual(FeedbackMessage.objects.count(), RATE_LIMIT)
        self.assertTrue(blocked.context["form"].non_field_errors())

        other_ip_response = self.client.post(
            self.form_url,
            data=self.valid_data,
            REMOTE_ADDR="203.0.113.10",
        )
        self.assertRedirects(other_ip_response, self.thanks_url)
        self.assertEqual(FeedbackMessage.objects.count(), RATE_LIMIT + 1)

    def test_thanks_page_renders(self):
        response = self.client.get(self.thanks_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "feedback/thanks.html")

    def test_disallowed_method_returns_405(self):
        response = self.client.put(self.form_url)
        self.assertEqual(response.status_code, 405)


class FeedbackAdminAndDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="strong-password-123",
        )
        cls.viewer = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="strong-password-123",
            is_staff=True,
        )
        view_perm = Permission.objects.get(codename="view_feedbackmessage")
        cls.viewer.user_permissions.add(view_perm)

        cls.staff_no_perms = User.objects.create_user(
            username="nobody",
            email="nobody@example.com",
            password="strong-password-123",
            is_staff=True,
        )

    def setUp(self):
        self.msg1 = FeedbackMessage.objects.create(
            email="one@example.com",
            message="Первое непрочитанное сообщение для проверки админки.",
        )
        self.msg2 = FeedbackMessage.objects.create(
            email="two@example.com",
            message="Второе сообщение, уже прочитанное ранее.",
            is_read=True,
        )

    def test_unread_badge_returns_count_or_empty_string(self):
        request = RequestFactory().get("/")
        self.assertEqual(unread_badge(request), 1)

        self.msg1.is_read = True
        self.msg1.save(update_fields=["is_read"])
        self.assertEqual(unread_badge(request), "")

    def test_latest_messages_table_respects_limit_and_statuses(self):
        table = latest_messages_table(limit=1)
        self.assertEqual(table["headers"], ["Получено", "Почта", "Сообщение", "Статус"])
        self.assertEqual(len(table["rows"]), 1)
        self.assertEqual(table["rows"][0][1], self.msg2.email)
        self.assertIn("Прочитано", table["rows"][0][3])

        full_table = latest_messages_table(limit=5)
        self.assertEqual(len(full_table["rows"]), 2)
        self.assertIn("Новое", full_table["rows"][1][3])

    def test_add_permission_is_disabled(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:feedback_feedbackmessage_add"))
        self.assertEqual(response.status_code, 403)

    def test_read_view_marks_message_as_read_and_returns_json(self):
        self.client.force_login(self.superuser)
        url = reverse("admin:feedback_feedbackmessage_read", args=[self.msg1.pk])

        self.assertEqual(self.client.get(url).status_code, 405)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.msg1.email)
        self.assertEqual(data["message"], self.msg1.message)
        self.assertTrue(data["was_unread"])
        self.assertEqual(data["unread"], 0)
        self.assertIn(f"mailto:{self.msg1.email}", data["reply_url"])

        self.msg1.refresh_from_db()
        self.assertTrue(self.msg1.is_read)

    def test_read_view_viewer_only_reads_without_mutating(self):
        self.client.force_login(self.viewer)
        url = reverse("admin:feedback_feedbackmessage_read", args=[self.msg1.pk])

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.msg1.refresh_from_db()
        self.assertFalse(self.msg1.is_read)

    def test_read_view_requires_view_permission(self):
        self.client.force_login(self.staff_no_perms)
        url = reverse("admin:feedback_feedbackmessage_read", args=[self.msg1.pk])

        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_bulk_view_updates_read_state_and_validates_input(self):
        self.client.force_login(self.superuser)
        url = reverse("admin:feedback_feedbackmessage_bulk")

        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, data={"action": "delete"}).status_code, 400)

        response = self.client.post(
            url,
            data={"action": "unread", "ids": [str(self.msg2.pk), "bad-id"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"changed": 1, "unread": 2})

        self.msg2.refresh_from_db()
        self.assertFalse(self.msg2.is_read)

    def test_bulk_view_requires_change_permission(self):
        self.client.force_login(self.viewer)
        url = reverse("admin:feedback_feedbackmessage_bulk")

        response = self.client.post(url, data={"action": "read", "ids": [str(self.msg1.pk)]})
        self.assertEqual(response.status_code, 403)

    def test_status_and_latest_views(self):
        self.client.force_login(self.viewer)

        status_response = self.client.get(reverse("admin:feedback_feedbackmessage_status"))
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(
            status_response.json(),
            {
                "unread": 1,
                "latest_id": self.msg2.pk,
                "latest_email": self.msg2.email,
            },
        )

        latest_response = self.client.get(reverse("admin:feedback_feedbackmessage_latest"))
        self.assertEqual(latest_response.status_code, 200)
        self.assertTemplateUsed(latest_response, "admin/includes/latest_messages.html")

        self.client.force_login(self.staff_no_perms)
        self.assertEqual(
            self.client.get(reverse("admin:feedback_feedbackmessage_status")).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse("admin:feedback_feedbackmessage_latest")).status_code,
            403,
        )

    def test_change_view_marks_message_as_read(self):
        self.client.force_login(self.superuser)
        url = reverse("admin:feedback_feedbackmessage_change", args=[self.msg1.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.msg1.refresh_from_db()
        self.assertTrue(self.msg1.is_read)

    def test_admin_changelist_search_handles_cyrillic_case(self):
        self.client.force_login(self.superuser)
        url = reverse("admin:feedback_feedbackmessage_changelist")

        response = self.client.get(url, {"q": "ПЕРВОЕ непрочитанное"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.msg1.email)
        self.assertNotContains(response, self.msg2.email)
