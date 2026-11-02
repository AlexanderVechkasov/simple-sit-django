"""Настройки для разработки на своём компьютере."""

from .base import *  # noqa: F403 — берём все общие настройки

# Если в .env не заполнен ALLOWED_HOSTS, всё равно разрешаем локальные адреса.
ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1"]  # noqa: F405
