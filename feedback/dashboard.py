"""Таблица «Последние сообщения» для «Сводки» в админке.

Нужна в двух местах: при открытии «Сводки» (timeline/dashboard.py)
и при её автообновлении (адрес …/feedbackmessage/latest/ в feedback/admin.py).
"""

from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import Truncator
from .models import FeedbackMessage

def latest_messages_table(limit=5):
    """Последние сообщения (и новые, и прочитанные) в формате таблицы Unfold.

    Клик по сообщению открывает окно «Прочитать» (static/js/admin-messages.js);
    без JavaScript ссылка просто ведёт на страницу сообщения.
    """
    rows = []
    # Порядок «сначала свежие» задан в модели (ordering = ["-created_at"]).
    for message in FeedbackMessage.objects.all()[:limit]:
        change_url = reverse("admin:feedback_feedbackmessage_change", args=[message.pk])
        read_url = reverse("admin:feedback_feedbackmessage_read", args=[message.pk])
        if message.is_read:
            status = format_html('<span class="message-status">{}</span>', "Прочитано")
        else:
            status = format_html('<span class="message-status is-unread">{}</span>', "Новое")
        rows.append([
            f"{timezone.localtime(message.created_at):%d.%m.%Y %H:%M}",
            message.email,
            format_html(
                '<a href="{}" class="message-link" data-url="{}">{}</a>',
                change_url,
                read_url,
                Truncator(message.message).chars(70),
            ),
            status,
        ])
    return {
        "headers": ["Получено", "Почта", "Сообщение", "Статус"],
        "rows": rows,
    }
