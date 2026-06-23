from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Episode, Show
from .serializers import EpisodeSerializer, ShowCardSerializer, ShowDetailSerializer


class CatalogView(APIView):
    """Browse grid — published shows only. Public metadata, no video."""
    permission_classes = [AllowAny]

    def get(self, request):
        shows = Show.objects.filter(status="published").order_by("-created_at")
        genre = request.query_params.get("genre")
        if genre:
            shows = [s for s in shows if genre in (s.genre or [])]
        return Response({"shows": ShowCardSerializer(shows, many=True).data})


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
