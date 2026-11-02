"""Главная карта адресов сайта."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    # Админка по адресу из .env (ADMIN_URL), а не по стандартному /admin/.
    path(settings.ADMIN_URL, admin.site.urls),
]

# При разработке Django сам отдаёт загруженные картинки из папки media/.
# На сервере этим займётся веб-сервер, поэтому только при DEBUG.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
