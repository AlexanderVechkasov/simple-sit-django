"""Главная карта адресов сайта."""

from django.conf import settings
from django.contrib import admin
from django.urls import path

urlpatterns = [
    # Админка по адресу из .env (ADMIN_URL), а не по стандартному /admin/.
    path(settings.ADMIN_URL, admin.site.urls),
]
