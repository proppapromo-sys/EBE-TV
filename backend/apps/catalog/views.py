from datetime import timedelta

from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Collection, CollectionItem, Episode, Show, WatchProgress
from .serializers import (CollectionSerializer, EpisodeSerializer, ShowCardSerializer,
                          ShowDetailSerializer)


def _row(title, slug, shows):
    """Build a browse row from a list/queryset of shows (skips empty rows)."""
    shows = [s for s in shows if s and s.status == "published"]
    return {"title": title, "slug": slug, "kind": "auto",
            "items": ShowCardSerializer(shows, many=True).data} if shows else None


def _continue_watching(user):
    if not (user and user.is_authenticated):
        return None
    seen, shows = set(), []
    wp = (WatchProgress.objects.filter(user=user, position_s__gt=0)
          .select_related("episode__season__show").order_by("-updated_at")[:40])
    for p in wp:
        show = p.episode.season.show
        if show.id not in seen and show.status == "published":
            seen.add(show.id)
            shows.append(show)
    return _row("Continue Watching", "continue", shows[:12])


def _trending():
    since = timezone.now() - timedelta(days=14)
    ranked = (WatchProgress.objects.filter(updated_at__gte=since)
              .values("episode__season__show")
              .annotate(n=Count("id")).order_by("-n")[:12])
    by_id = {s.id: s for s in Show.objects.filter(
        id__in=[r["episode__season__show"] for r in ranked])}
    return _row("Trending Now", "trending",
                [by_id.get(r["episode__season__show"]) for r in ranked])


def _new():
    return _row("New on EBE", "new",
                list(Show.objects.filter(status="published").order_by("-created_at")[:12]))


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
        hero, curated = [], []
        for c in collections:
            data = CollectionSerializer(c).data
            if not data["items"]:
                continue                      # don't render empty rows
            if c.kind == Collection.HERO:
                hero.extend(data["items"])
            else:
                curated.append(data)
        # Personalized / computed rows around the editor's curated ones.
        rows = [r for r in [_continue_watching(request.user)] if r] \
            + curated + [r for r in [_trending(), _new()] if r]
        return Response({"hero": hero, "rows": rows})


class SearchView(APIView):
    """Public search over published shows — title/description/genre, with an optional genre facet."""
    permission_classes = [AllowAny]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        genre = (request.query_params.get("genre") or "").strip()
        published = Show.objects.filter(status="published")

        # Genre facet over the whole published catalog (so the UI can offer filter chips).
        facets = sorted({g for gs in published.values_list("genre", flat=True) for g in (gs or [])})
        if not q and not genre:
            return Response({"query": q, "results": [], "genres": facets})

        shows = published
        if q:
            shows = shows.filter(Q(title__icontains=q) | Q(description__icontains=q))
        results = list(shows.order_by("-created_at")[:100])
        if q:                                  # also match shows tagged with a genre named like q
            extra = [s for s in published.order_by("-created_at")
                     if any(q.lower() in g.lower() for g in (s.genre or [])) and s not in results]
            results = (results + extra)[:100]
        if genre:
            results = [s for s in results if genre in (s.genre or [])]
        return Response({"query": q, "genre": genre, "genres": facets,
                         "results": ShowCardSerializer(results[:50], many=True).data})


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
