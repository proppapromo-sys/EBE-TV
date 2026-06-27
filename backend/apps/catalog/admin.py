from django.contrib import admin

from .models import (Collection, CollectionItem, Episode, Season, Show, Video,
                     WatchProgress)


class CollectionItemInline(admin.TabularInline):
    model = CollectionItem
    extra = 1
    raw_id_fields = ("show",)
    ordering = ("position",)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "position", "published")
    list_editable = ("position", "published")
    list_filter = ("kind", "published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CollectionItemInline]


class SeasonInline(admin.TabularInline):
    model = Season
    extra = 1


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "owner", "status", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("status",)
    list_select_related = ("owner",)
    raw_id_fields = ("owner",)
    search_fields = ("title", "owner__email")
    inlines = [SeasonInline]


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ("title", "season", "number", "status", "published_at")
    list_filter = ("status",)


admin.site.register(Video)
admin.site.register(Season)
admin.site.register(WatchProgress)
