"""
Общие настройки проекта — одинаковые для разработки и для сервера.
Секреты и всё, что отличается между компьютерами, читаем из файла .env.
"""

from pathlib import Path

import environ

# Корень проекта — папка, где лежит manage.py.
# Этот файл лежит в config/settings/base.py, поэтому поднимаемся на три уровня.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Читаем .env, если он есть. На сервере переменные можно задать и без файла.
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# Секретный ключ — только из окружения. Если его нет, Django не запустится.
SECRET_KEY = env("SECRET_KEY")

# Отладка выключена по умолчанию, включается только явно в .env.
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Адрес админки (не стандартный /admin/). Обязателен в .env.
ADMIN_URL = env("ADMIN_URL")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Чтобы runserver отдавал статику так же, как сервер (через WhiteNoise).
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "timeline",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Общая папка шаблонов в корне проекта (создадим на этапе 4).
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# База для разработки — SQLite, один файл в корне проекта.
# На сервере её заменяет prod.py через DATABASE_URL.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Язык и время: русский интерфейс (в том числе админки), московское время.
LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# Статика (CSS, JS, иконки).
STATIC_URL = "static/"
# Где лежат наши исходные файлы статики.
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Загруженные файлы — картинки событий.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
