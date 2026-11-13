"""
Общие настройки проекта — одинаковые для разработки и для сервера.
Секреты и всё, что отличается между компьютерами, читаем из файла .env.
"""

from pathlib import Path
import environ
from django.templatetags.static import static
from django.urls import reverse_lazy

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
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Чтобы runserver отдавал статику так же, как сервер (через WhiteNoise).
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "timeline",
    "feedback",
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
# Свои переводы проекта (например, надписи Unfold) — в папке locale/
LOCALE_PATHS = [BASE_DIR / "locale"]

# Статика (CSS, JS, иконки).
STATIC_URL = "static/"
# Где лежат наши исходные файлы статики.
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Загруженные файлы — картинки событий.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Оформление админки (Unfold): название, цвета и боковое меню.
UNFOLD = {
    "SITE_TITLE": "Историческая шкала",
    "SITE_HEADER": "Историческая шкала",
    "SITE_SUBHEADER": "Панель управления",
    "SITE_SYMBOL": "history_edu",  # значок из набора Material Symbols
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
# Данные для «Сводки» на главной странице админки
    "DASHBOARD_CALLBACK": "timeline.dashboard.dashboard_callback",
# Наш CSS поверх оформления Unfold
    "STYLES": [lambda request: static("css/admin.css")],
    "SCRIPTS": [
        lambda request: static("js/admin-live.js"),
        lambda request: static("js/admin-messages.js"),
    ],
    # Основной цвет — тёмно-синий, как на сайте. Оттенки от светлого (50)
    # до тёмного (950) в формате oklch; Unfold сам выбирает нужные.
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
    # Боковое меню: свои разделы, названия и значки.
    "SIDEBAR": {
        "show_search": True,
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
                        # Число непрочитанных — функция в feedback/admin.py
                        "badge": "feedback.admin.unread_badge",
                        # Адрес, который admin-live.js опрашивает раз в 20 секунд
                        "link_attrs": {"data-status-url": reverse_lazy("admin:feedback_feedbackmessage_status")},
                    },
                ],
            },
            {
                "title": "Доступ",
                "collapsible": True,  # раздел можно свернуть
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
