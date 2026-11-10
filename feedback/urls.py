"""Адреса приложения feedback."""

from django.urls import path

from . import views

app_name = "feedback"

urlpatterns = [
    path("feedback/", views.feedback, name="form"),
    path("feedback/thanks/", views.thanks, name="thanks"),
]
