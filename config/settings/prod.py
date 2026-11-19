"""Настройки для сервера. HTTPS, HSTS и CSP"""

from .base import *  # noqa: F403 — берём все общие настройки

# На сервере отладка выключена всегда, что бы ни было в окружении.
DEBUG = False

# База на сервере — из переменной DATABASE_URL (например, PostgreSQL).
DATABASES = {"default": env.db("DATABASE_URL")}  # noqa: F405

# Статика на сервере: WhiteNoise сжимает файлы и добавляет к именам
# «отпечаток» (styles.3f2a1c.css). Браузер кэширует их надолго,
# а после изменения файла сразу получает новую версию.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
