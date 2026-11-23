"""Админка: события с изображениями, а также пользователи и группы."""

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import Event, EventImage
from .search import search_events


class CenturyFilter(admin.SimpleListFilter):
    """Фильтр событий по векам (по году начала)."""

    title = "век"
    parameter_name = "century"

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


class HasImageFilter(admin.SimpleListFilter):
    """Фильтр по наличию хотя бы одного изображения у события."""

    title = "изображение"
    parameter_name = "has_image"

    def lookups(self, request, model_admin):
        return [("yes", "есть"), ("no", "нет")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(images__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(images__isnull=True)
        return queryset


class EventImageInline(TabularInline):
    model = EventImage
    extra = 1
    tab = True
    fields = ["preview", "image", "caption", "source", "order"]
    readonly_fields = ["preview"]

    @admin.display(description="превью")
    def preview(self, obj):
        # При повторном показе формы с ошибкой у несохранённой картинки ещё нет pk и файла на диске.
        if obj.pk and obj.image:
            return format_html('<img src="{}" alt="" class="admin-thumb">', obj.image.url)
        return "—"


@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ["thumbnail", "years", "title", "region", "outcome_label", "order"]
    list_display_links = ["thumbnail", "years", "title"]
    list_editable = ["order"]

    class Media:
        js = ["js/admin-list-toolbar.js"]

    list_filter = [CenturyFilter, "outcome", HasImageFilter]
    search_fields = ["title", "summary", "body", "region", "key", "start_year", "end_year"]
    search_help_text = "Поиск по году, названию, региону, ключу или тексту статьи"
    list_per_page = 30

    prepopulated_fields = {"slug": ["start_year", "title"]}
    readonly_fields = ["created_at", "updated_at"]
    inlines = [EventImageInline]

    fieldsets = [
        (
            "Основное",
            {
                "classes": ["tab"],
                "fields": ["title", ("start_year", "end_year"), "region", "outcome"],
            },
        ),
        (
            "Тексты",
            {
                "classes": ["tab"],
                "fields": ["summary", "body"],
            },
        ),
        (
            "Адрес и порядок",
            {
                "classes": ["tab"],
                "fields": ["slug", "key", "order", ("created_at", "updated_at")],
            },
        ),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("images")

    def get_search_results(self, request, queryset, search_term):
        # SQLite не поддерживает регистронезависимый LIKE для кириллицы,
        # поэтому фильтруем через общий поиск с casefold и ё → е.
        if not search_term.strip():
            return queryset, False
        matched_ids = [
            event.pk
            for event in search_events(search_term, queryset=queryset, include_internal=True)
        ]
        return queryset.filter(pk__in=matched_ids), False

    @admin.display(description="годы", ordering="start_year")
    def years(self, obj):
        return obj.years_display

    @admin.display(description="")
    def thumbnail(self, obj):
        images = obj.images.all()
        if images:
            return format_html('<img src="{}" alt="" class="admin-thumb">', images[0].image.url)
        return "—"

    @display(
        description="итог",
        ordering="outcome",
        label={
            Event.Outcome.VICTORY: "success",
            Event.Outcome.DEFEAT: "danger",
            Event.Outcome.DRAW: "warning",
            Event.Outcome.UNDETERMINED: "info",
        },
    )
    def outcome_label(self, obj):
        if not obj.outcome:
            return None
        return obj.outcome, obj.get_outcome_display()


admin.site.index_title = "Сводка"

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
