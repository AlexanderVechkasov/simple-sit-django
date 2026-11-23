"""Настройки для production-окружения."""

from .base import *  # noqa: F403

DEBUG = False

DATABASES = {"default": env.db("DATABASE_URL")}  # noqa: F405

# За обратным прокси (PythonAnywhere / nginx) доверяем заголовкам прокси и схеме HTTPS.
TRUST_PROXY_HEADERS = env.bool("TRUST_PROXY_HEADERS", default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Весь наш JS берёт CSRF-токен из скрытого <input>, а не из document.cookie.
CSRF_COOKIE_HTTPONLY = True

# Умеренный HSTS без includeSubDomains/preload — безопасно для поддомена *.pythonanywhere.com.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)  # noqa: F405
SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
