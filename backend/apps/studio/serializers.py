from rest_framework import serializers

from apps.catalog.models import Episode, Season, Show


class StudioEpisodeSerializer(serializers.ModelSerializer):
    ready = serializers.BooleanField(source="video.ready", read_only=True, default=False)

    class Meta:
        model = Episode
        fields = ("id", "season", "number", "title", "description", "thumbnail_url",
                  "duration_s", "video", "status", "ready")
        read_only_fields = ("id", "status")        # publishing is gated; not creator-settable


class StudioSeasonSerializer(serializers.ModelSerializer):
    episodes = StudioEpisodeSerializer(many=True, read_only=True)

    class Meta:
        model = Season
        fields = ("id", "show", "number", "title", "episodes")
        read_only_fields = ("id",)


class StudioShowSerializer(serializers.ModelSerializer):
    seasons = StudioSeasonSerializer(many=True, read_only=True)

    class Meta:
        model = Show
        fields = ("id", "title", "slug", "description", "poster_url", "hero_url",
                  "genre", "status", "seasons", "created_at")
        # slug + owner are set server-side; status changes only via submit/moderation.
        read_only_fields = ("id", "slug", "status", "created_at")
