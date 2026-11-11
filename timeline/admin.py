"""Админка: события с изображениями, а также пользователи и группы."""

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import Event, EventImage


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


class EventImageInline(TabularInline):
    """Картинки события — на отдельной вкладке «Изображения»."""

    model = EventImage
    extra = 1  # одна пустая строка для новой картинки
    tab = True  # показать отдельной вкладкой (возможность Unfold)
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
class EventAdmin(ModelAdmin):
    # Столбцы в списке событий.
    list_display = ["years", "title", "region", "outcome", "order"]
    list_display_links = ["years", "title"]
    # Порядок можно менять прямо в списке, не открывая событие.
    list_editable = ["order"]
    list_filter = [CenturyFilter, "outcome"]
    search_fields = ["title", "summary", "region", "key"]
    list_per_page = 30

    # При создании события адрес заполняется сам из года и заголовка.
    prepopulated_fields = {"slug": ["start_year", "title"]}
    readonly_fields = ["created_at", "updated_at"]
    inlines = [EventImageInline]

    # Поля события разложены по вкладкам (classes: ["tab"] — возможность Unfold).
    fieldsets = [
        ("Основное", {
            "classes": ["tab"],
            "fields": ["title", ("start_year", "end_year"), "region", "outcome"],
        }),
        ("Тексты", {
            "classes": ["tab"],
            "fields": ["summary", "body"],
        }),
        ("Адрес и порядок", {
            "classes": ["tab"],
            "fields": ["slug", "key", "order", ("created_at", "updated_at")],
        }),
    ]

    @admin.display(description="годы", ordering="start_year")
    def years(self, obj):
        return obj.years_display


# Пользователи и группы: те же стандартные страницы Django, но в оформлении Unfold.
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
