from rest_framework import serializers

from .models import Collection, Episode, Season, Show


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


def _first_episode_thumb(show):
    ep = (Episode.objects.filter(season__show=show, status="published")
          .exclude(thumbnail_url="").order_by("season__number", "number").first())
    return ep.thumbnail_url if ep else ""


class ShowCardSerializer(serializers.ModelSerializer):
    # Never blank: fall back poster → hero → an episode thumbnail (the web renders a branded
    # placeholder if all are empty).
    poster_url = serializers.SerializerMethodField()

    class Meta:
        model = Show
        fields = ("id", "title", "slug", "poster_url", "hero_url", "genre")

    def get_poster_url(self, obj):
        return obj.poster_url or obj.hero_url or _first_episode_thumb(obj)


class CollectionSerializer(serializers.ModelSerializer):
    """A browse row with its ordered, published shows."""
    items = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ("title", "slug", "kind", "items")

    def get_items(self, obj):
        shows = [it.show for it in obj.items.all() if it.show.status == "published"]
        return ShowCardSerializer(shows, many=True).data


class ShowDetailSerializer(serializers.ModelSerializer):
    seasons = SeasonSerializer(many=True, read_only=True)

    class Meta:
        model = Show
        fields = ("id", "title", "slug", "description", "poster_url", "hero_url",
                  "genre", "seasons")
