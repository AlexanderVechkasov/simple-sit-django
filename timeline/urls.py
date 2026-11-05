"""Адреса приложения timeline."""

from django.urls import path
from . import views

# Пространство имён: в шаблонах пишем {% url "timeline:index" %}.
app_name = "timeline"

urlpatterns = [
    path("", views.timeline, name="index"),
    # Сначала короткий адрес из одних цифр (/events/1914/)…
    path("events/<int:year>/", views.event_by_year, name="event_by_year"),
    # …потом полный адрес статьи (/events/1914-pervaya-mirovaya-voyna/).
    path("events/<slug:slug>/", views.event_detail, name="event_detail"),
]
