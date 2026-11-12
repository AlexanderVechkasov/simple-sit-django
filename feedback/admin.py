"""Чтение сообщений обратной связи в админке."""

from urllib.parse import quote

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import Truncator
from unfold.admin import ModelAdmin

from .models import FeedbackMessage

# Тема письма, когда нажимаешь «Ответить»
REPLY_SUBJECT = "Re: Историческая шкала России"


def unread_badge(request):
    """Число непрочитанных сообщений — для значка в боковом меню.

    Пустая строка вместо нуля: значок не показывается, когда всё прочитано.
    """
    count = FeedbackMessage.objects.filter(is_read=False).count()
    return count or ""


@admin.register(FeedbackMessage)
class FeedbackMessageAdmin(ModelAdmin):
    list_display = ["created_at", "email", "short_message", "is_read", "read_button"]
    list_display_links = ["created_at", "email"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["email", "message"]
    date_hierarchy = "created_at"  # навигация по датам над списком

    # Сообщение посетителя не редактируем — только читаем и отмечаем.
    fields = ["created_at", "email", "message", "is_read"]
    readonly_fields = ["created_at", "email", "message"]
    actions = ["mark_as_read", "mark_as_unread"]

    class Media:
        # Окно «Прочитать» в списке сообщений
        js = ["js/admin-messages.js"]

    @admin.display(description="сообщение")
    def short_message(self, obj):
        """Первые 80 символов сообщения для списка."""
        return Truncator(obj.message).chars(80)

    @admin.display(description="")
    def read_button(self, obj):
        """Кнопка, которая открывает сообщение во всплывающем окне."""
        url = reverse("admin:feedback_feedbackmessage_read", args=[obj.pk])
        return format_html(
            '<button type="button" class="message-open" data-url="{}">Прочитать</button>',
            url,
        )

    def get_urls(self):
        """Свой адрес в админке: …/feedbackmessage/<номер>/read/."""
        custom_urls = [
            path(
                "<int:pk>/read/",
                # admin_view: только для вошедших в админку + защита CSRF
                self.admin_site.admin_view(self.read_view),
                name="feedback_feedbackmessage_read",
            ),
        ]
        # Свои адреса — первыми, иначе их перехватят стандартные.
        return custom_urls + super().get_urls()

    def read_view(self, request, pk):
        """Отдаёт сообщение окну «Прочитать» и отмечает его прочитанным."""
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        message = get_object_or_404(FeedbackMessage, pk=pk)
        if not self.has_view_permission(request, message):
            raise PermissionDenied

        was_unread = not message.is_read
        if was_unread and self.has_change_permission(request, message):
            message.is_read = True
            message.save(update_fields=["is_read"])

        received = timezone.localtime(message.created_at)
        return JsonResponse({
            "email": message.email,
            "received": f"{received:%d.%m.%Y %H:%M}",
            "message": message.message,
            "was_unread": was_unread,
            "reply_url": f"mailto:{message.email}?subject={quote(REPLY_SUBJECT)}",
            "change_url": reverse("admin:feedback_feedbackmessage_change", args=[message.pk]),
        })

    def has_add_permission(self, request):
        # Сообщения приходят только с сайта, вручную их не создаём.
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Открыл сообщение — оно автоматически отмечается прочитанным.
        FeedbackMessage.objects.filter(pk=object_id, is_read=False).update(is_read=True)
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.action(description="Отметить как прочитанные")
    def mark_as_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f"Отмечено как прочитанные: {count}.")

    @admin.action(description="Отметить как непрочитанные")
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False)
        self.message_user(request, f"Отмечено как непрочитанные: {count}.")
