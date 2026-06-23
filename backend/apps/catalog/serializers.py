from rest_framework import serializers

from .models import Episode, Season, Show


class EpisodeSerializer(serializers.ModelSerializer):
    """Episode METADATA only — never includes video URLs or the Stream UID. Playback comes
    exclusively from the entitlement-gated /api/play/{id} endpoint."""
    ready = serializers.SerializerMethodField()

    class Meta:
        model = Episode
        fields = ("id", "number", "title", "description", "thumbnail_url",
                  "duration_s", "status", "published_at", "ready")

    def get_ready(self, obj):
        return bool(obj.video and obj.video.ready)


class SeasonSerializer(serializers.ModelSerializer):
    episodes = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = ("id", "number", "title", "episodes")

    def get_episodes(self, obj):
        qs = obj.episodes.filter(status="published")
        return EpisodeSerializer(qs, many=True).data


class ShowCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Show
        fields = ("id", "title", "slug", "poster_url", "hero_url", "genre")


class ShowDetailSerializer(serializers.ModelSerializer):
    seasons = SeasonSerializer(many=True, read_only=True)

    class Meta:
        model = Show
        fields = ("id", "title", "slug", "description", "poster_url", "hero_url",
                  "genre", "seasons")
