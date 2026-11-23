"""Настройки для production-окружения."""

from .base import *  # noqa: F403

DEBUG = False

DATABASES = {"default": env.db("DATABASE_URL")}  # noqa: F405

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
