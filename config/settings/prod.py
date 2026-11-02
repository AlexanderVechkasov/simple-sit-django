"""Настройки для сервера. HTTPS, HSTS и CSP """

from .base import *  # noqa: F403 — берём все общие настройки

# На сервере отладка выключена всегда, что бы ни было в окружении.
DEBUG = False

# База на сервере — из переменной DATABASE_URL (например, PostgreSQL).
DATABASES = {"default": env.db("DATABASE_URL")}  # noqa: F405
