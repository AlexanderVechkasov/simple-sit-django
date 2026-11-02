"""Настройка админки для событий и изображений."""

from django.contrib import admin
from django.utils.html import format_html

from .models import Event, EventImage

# Заголовки админки вместо стандартного «Администрирование Django».
admin.site.site_header = "Историческая шкала России"
admin.site.site_title = "Историческая шкала"
admin.site.index_title = "Управление сайтом"


class CenturyFilter(admin.SimpleListFilter):
    """Фильтр справа в списке: события по векам (по году начала)."""

    title = "век"
    parameter_name = "century"

    # Век: (от года, до года) включительно.
    CENTURIES = {
        "18": ("XVIII век", 1701, 1800),
        "19": ("XIX век", 1801, 1900),
        "20": ("XX век", 1901, 2000),
    }

    def lookups(self, request, model_admin):
        return [(code, label) for code, (label, _, _) in self.CENTURIES.items()]

    def queryset(self, request, queryset):
        if self.value() in self.CENTURIES:
            _, start, end = self.CENTURIES[self.value()]
            return queryset.filter(start_year__gte=start, start_year__lte=end)
        return queryset


class EventImageInline(admin.TabularInline):
    """Картинки редактируются прямо на странице события, таблицей внизу."""

    model = EventImage
    extra = 1  # одна пустая строка для новой картинки
    fields = ["preview", "image", "caption", "source", "order"]
    readonly_fields = ["preview"]

    @admin.display(description="превью")
    def preview(self, obj):
        if obj.image:
            # format_html безопасно подставляет значения в HTML.
            return format_html(
                '<img src="{}" alt="" style="max-height: 80px; max-width: 120px;">',
                obj.image.url,
            )
        return "—"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # Столбцы в списке событий.
    list_display = ["years", "title", "region", "outcome", "order"]
    list_display_links = ["years", "title"]
    # Порядок можно менять прямо в списке, не открывая событие.
    list_editable = ["order"]
    list_filter = [CenturyFilter, "outcome"]
    search_fields = ["title", "summary", "region", "key"]
    list_per_page = 30

    # При создании события адрес заполняется сам из года и заголовка
    # (Django переводит кириллицу в латиницу).
    prepopulated_fields = {"slug": ["start_year", "title"]}
    readonly_fields = ["created_at", "updated_at"]
    inlines = [EventImageInline]

    # Поля на странице события, разбитые на блоки.
    fieldsets = [
        (None, {"fields": ["title", ("start_year", "end_year"), "slug", "key"]}),
        ("Описание", {"fields": ["summary", "region", "outcome", "body"]}),
        ("Служебное", {"fields": ["order", ("created_at", "updated_at")]}),
    ]

    @admin.display(description="годы", ordering="start_year")
    def years(self, obj):
        return obj.years_display
