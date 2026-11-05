"""Адреса приложения timeline."""

from django.urls import path

from . import views

# Пространство имён: в шаблонах пишем {% url "timeline:index" %}.
app_name = "timeline"

urlpatterns = [
    path("", views.timeline, name="index"),
]
