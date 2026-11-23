"""Сводка на главной странице админки (подключена в UNFOLD["DASHBOARD_CALLBACK"])."""

from django.urls import reverse

from feedback.dashboard import latest_messages_table
from feedback.models import FeedbackMessage

from .models import Event

ROMAN = {17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX", 21: "XXI"}


def dashboard_callback(request, context):
    """Добавляет в главную страницу админки карточки с цифрами
    и таблицу непрочитанных сообщений."""
    events_url = reverse("admin:timeline_event_changelist")
    messages_url = reverse("admin:feedback_feedbackmessage_changelist")

    by_century = {}
    for year in Event.objects.values_list("start_year", flat=True):
        century = (year - 1) // 100 + 1
        by_century[century] = by_century.get(century, 0) + 1
    centuries = " · ".join(f"{ROMAN.get(c, c)} — {n}" for c, n in sorted(by_century.items()))

    without_images = Event.objects.filter(images__isnull=True).count()
    unread = FeedbackMessage.objects.filter(is_read=False)

    context["stats"] = [
        {
            "title": "Событий на шкале",
            "value": sum(by_century.values()),
            "note": centuries,
            "icon": "timeline",
            "url": events_url,
        },
        {
            "title": "Без изображения",
            "value": without_images,
            "note": "Можно добавить картинку" if without_images else "У всех событий есть картинка",
            "icon": "image",
            "url": f"{events_url}?has_image=no",
        },
        {
            "title": "Непрочитанных сообщений",
            "value": unread.count(),
            "note": "Обратная связь с сайта",
            "icon": "mail",
            "url": messages_url,
            "live": True,
        },
    ]

    context["latest_messages"] = latest_messages_table()
    return context
