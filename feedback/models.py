"""Сообщения, отправленные через форму обратной связи на сайте."""

from django.db import models
from django.utils import timezone


class FeedbackMessage(models.Model):
    """Одно сообщение от посетителя сайта."""

    name = models.CharField("имя", max_length=100)
    email = models.EmailField("электронная почта")
    message = models.TextField("сообщение", max_length=3000)
    created_at = models.DateTimeField("получено", auto_now_add=True)
    is_read = models.BooleanField("прочитано", default=False)

    class Meta:
        ordering = ["-created_at"]  # новые сверху
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"

    def __str__(self):
        # localtime переводит время из UTC (так оно хранится в базе) в московское
        received = timezone.localtime(self.created_at)
        return f"{self.name}, {received:%d.%m.%Y %H:%M}"
