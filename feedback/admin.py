"""Чтение сообщений обратной связи в админке."""

from django.contrib import admin
from django.utils.text import Truncator
from unfold.admin import ModelAdmin
from .models import FeedbackMessage


def unread_badge(request):
    """Число непрочитанных сообщений — для значка в боковом меню.

    Пустая строка вместо нуля: значок не показывается, когда всё прочитано.
    """
    count = FeedbackMessage.objects.filter(is_read=False).count()
    return count or ""


@admin.register(FeedbackMessage)
class FeedbackMessageAdmin(ModelAdmin):
    list_display = ["created_at", "email", "short_message", "is_read"]
    list_display_links = ["created_at", "email"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["email", "message"]
    date_hierarchy = "created_at"  # навигация по датам над списком

    # Сообщение посетителя не редактируем — только читаем и отмечаем.
    fields = ["created_at", "email", "message", "is_read"]
    readonly_fields = ["created_at", "email", "message"]
    actions = ["mark_as_read", "mark_as_unread"]

    @admin.display(description="сообщение")
    def short_message(self, obj):
        """Первые 80 символов сообщения для списка."""
        return Truncator(obj.message).chars(80)

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
