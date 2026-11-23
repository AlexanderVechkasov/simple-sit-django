# Деплой на PythonAnywhere (бесплатный тариф)

Инструкция рассчитана на аккаунт `alexks09` (`https://alexks09.pythonanywhere.com`).

## 1. Проверка версии Python

Откройте **Account → System image** и убедитесь, что выбран образ `innit` (поддерживает Python 3.13).

## 2. Клонирование проекта и виртуальное окружение

Откройте **Consoles → Bash** и выполните:

```bash
git clone <URL-вашего-репозитория> ~/simple-sit-django
cd ~/simple-sit-django
python3.13 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
```

> Флаг `--no-cache-dir` экономит ~50 МБ из бесплатной квоты диска (512 МБ).

## 3. Создание `.env` на сервере

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Откройте `.env` (`nano .env` или через вкладку **Files**), вставьте сгенерированный `SECRET_KEY`, задайте свой нестандартный `ADMIN_URL` (со слэшем на конце) и проверьте `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`.

## 4. База данных, медиафайлы и статика

Если нужно перенести готовые события и картинки с компьютера:
- Загрузите `db.sqlite3` в `/home/alexks09/simple-sit-django/` через вкладку **Files** (или примените миграции на чистой базе и создайте суперпользователя).
- Запакуйте локальную папку `media/` в zip-архив (предварительно удалив лишние тестовые картинки, если они есть), загрузите в `/home/alexks09/simple-sit-django/` и распакуйте:
  ```bash
  unzip media.zip && rm media.zip
  ```

Затем в активированном `.venv` выполните:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Если база новая, создайте администратора:

```bash
python manage.py createsuperuser
```

## 5. Настройка Web-приложения

Откройте вкладку **Web → Add a new web app**:
1. Домен: `alexks09.pythonanywhere.com`.
2. Выберите **Manual configuration** (не Django wizard) → **Python 3.13**.
3. В разделе **Code**:
   - **Source code:** `/home/alexks09/simple-sit-django`
   - **Working directory:** `/home/alexks09/simple-sit-django`
4. В разделе **Virtualenv**:
   - Укажите `/home/alexks09/simple-sit-django/.venv`
5. Откройте **WSGI configuration file** (`/var/www/alexks09_pythonanywhere_com_wsgi.py`), замените содержимое на:

   ```python
   import os
   import sys

   path = "/home/alexks09/simple-sit-django"
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"

   from django.core.wsgi import get_wsgi_application

   application = get_wsgi_application()
   ```

6. В разделе **Static files** добавьте две строки:
   - URL: `/static/` → Directory: `/home/alexks09/simple-sit-django/staticfiles`
   - URL: `/media/` → Directory: `/home/alexks09/simple-sit-django/media`
7. В разделе **Security** включите **Force HTTPS**.
8. Нажмите зелёную кнопку **Reload alexks09.pythonanywhere.com**.

## 6. Как обновлять сайт после новых коммитов

```bash
cd ~/simple-sit-django
source .venv/bin/activate
git pull
pip install --no-cache-dir -r requirements.txt
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py migrate
python manage.py collectstatic --noinput
```

После этого нажмите **Reload** на вкладке **Web**.
