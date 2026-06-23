from django.contrib import admin

from .models import Episode, Season, Show, Video, WatchProgress


class SeasonInline(admin.TabularInline):
    model = Season
    extra = 1


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("status",)
    inlines = [SeasonInline]


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ("title", "season", "number", "status", "published_at")
    list_filter = ("status",)


admin.site.register(Video)
admin.site.register(Season)
admin.site.register(WatchProgress)
