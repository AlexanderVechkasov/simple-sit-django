"""Адреса приложения timeline."""

from django.urls import path

from . import views

app_name = "timeline"

urlpatterns = [
    path("", views.timeline, name="index"),
    # <int:year> должен идти перед <slug:slug>, иначе числовой год перехватит slug.
    path("events/<int:year>/", views.event_by_year, name="event_by_year"),
    path("events/<slug:slug>/", views.event_detail, name="event_detail"),
]
