"""Базовые настройки проекта, общие для dev и prod окружений."""

from pathlib import Path

import environ
from django.templatetags.static import static
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
TRUST_PROXY_HEADERS = env.bool("TRUST_PROXY_HEADERS", default=False)
ADMIN_URL = env("ADMIN_URL")

INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Перед staticfiles, чтобы runserver отдавал статику через WhiteNoise.
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "timeline",
    "feedback",
    # Должен идти последним, чтобы корректно перехватывать сигналы удаления файлов.
    "django_cleanup.apps.CleanupConfig",
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

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

UNFOLD = {
    "SITE_TITLE": "Историческая шкала",
    "SITE_HEADER": "Историческая шкала",
    "SITE_SUBHEADER": "Панель управления",
    "SITE_SYMBOL": "history_edu",
    "LOGIN": {"image": "timeline.login.random_login_image"},
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "DASHBOARD_CALLBACK": "timeline.dashboard.dashboard_callback",
    "STYLES": [lambda request: static("css/admin.css")],
    "SCRIPTS": [
        lambda request: static("js/admin-live.js"),
        lambda request: static("js/admin-messages.js"),
        lambda request: static("js/admin-theme-sync.js"),
        lambda request: static("js/admin-delete-confirm.js"),
    ],
    "COLORS": {
        "primary": {
            "50": "oklch(97% 0.014 254.604)",
            "100": "oklch(93.2% 0.032 255.585)",
            "200": "oklch(88.2% 0.059 254.128)",
            "300": "oklch(80.9% 0.105 251.813)",
            "400": "oklch(62.3% 0.214 259.815)",
            "500": "oklch(54.6% 0.245 262.881)",
            "600": "oklch(42.4% 0.199 265.638)",
            "700": "oklch(37.9% 0.146 265.522)",
            "800": "oklch(28.2% 0.091 267.935)",
            "900": "oklch(24% 0.075 268)",
            "950": "oklch(19% 0.06 268)",
        },
    },
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Историческая шкала",
                "items": [
                    {
                        "title": "События",
                        "icon": "timeline",
                        "link": reverse_lazy("admin:timeline_event_changelist"),
                    },
                ],
            },
            {
                "title": "Обратная связь",
                "items": [
                    {
                        "title": "Сообщения",
                        "icon": "mail",
                        "link": reverse_lazy("admin:feedback_feedbackmessage_changelist"),
                        "badge": "feedback.admin.unread_badge",
                        # Эндпоинт периодического опроса из static/js/admin-live.js.
                        "link_attrs": {
                            "data-status-url": reverse_lazy(
                                "admin:feedback_feedbackmessage_status"
                            ),
                        },
                    },
                ],
            },
            {
                "title": "Доступ",
                "collapsible": True,
                "items": [
                    {
                        "title": "Пользователи",
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": "Группы",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
}
