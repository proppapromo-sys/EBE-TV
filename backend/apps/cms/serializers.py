from rest_framework import serializers

from apps.catalog.models import Episode, Show


class ShowWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Show
        fields = ("id", "title", "slug", "description", "poster_url", "hero_url",
                  "genre", "status")
        read_only_fields = ("id",)


class EpisodeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Episode
        fields = ("id", "season", "number", "title", "description", "thumbnail_url",
                  "duration_s", "video", "status")
        read_only_fields = ("id",)
