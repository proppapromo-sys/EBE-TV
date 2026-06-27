from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Collection, CollectionItem, Episode, Show
from .serializers import (CollectionSerializer, EpisodeSerializer, ShowCardSerializer,
                          ShowDetailSerializer)


class CatalogView(APIView):
    """Browse grid — published shows only. Public metadata, no video."""
    permission_classes = [AllowAny]

    def get(self, request):
        shows = Show.objects.filter(status="published").order_by("-created_at")
        genre = request.query_params.get("genre")
        if genre:
            shows = [s for s in shows if genre in (s.genre or [])]
        return Response({"shows": ShowCardSerializer(shows, many=True).data})


class HomeView(APIView):
    """The browse home — a hero rail + ordered, editor-curated rows (NowThatsTV-style)."""
    permission_classes = [AllowAny]

    def get(self, request):
        published_items = Prefetch(
            "items", queryset=CollectionItem.objects.select_related("show").order_by("position"))
        collections = (Collection.objects.filter(published=True)
                       .prefetch_related(published_items).order_by("position", "title"))
        hero, rows = [], []
        for c in collections:
            data = CollectionSerializer(c).data
            if not data["items"]:
                continue                      # don't render empty rows
            if c.kind == Collection.HERO:
                hero.extend(data["items"])
            else:
                rows.append(data)
        return Response({"hero": hero, "rows": rows})


class SearchView(APIView):
    """Public title/description search over published shows."""
    permission_classes = [AllowAny]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response({"query": q, "results": []})
        shows = (Show.objects.filter(status="published")
                 .filter(Q(title__icontains=q) | Q(description__icontains=q))
                 .order_by("-created_at")[:50])
        return Response({"query": q, "results": ShowCardSerializer(shows, many=True).data})


class ShowDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        show = get_object_or_404(Show, slug=slug, status="published")
        return Response(ShowDetailSerializer(show).data)


class EpisodeDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, episode_id):
        ep = get_object_or_404(Episode, id=episode_id, status="published")
        return Response(EpisodeSerializer(ep).data)
