"""
Creator studio — self-serve upload. Everything here is scoped to the requesting creator: you can
only see and edit shows you own, and you cannot publish yourself (submit → moderation → publish).

  POST /api/studio/enable            become a creator
  GET  /api/studio/shows             list my shows
  POST /api/studio/shows             create / update one of my shows
  POST /api/studio/seasons           add a season to my show
  POST /api/studio/episodes          create / update an episode on my show
  POST /api/studio/videos/upload-url get a Cloudflare direct-upload URL (+ a Video row)
  POST /api/studio/submit            submit a show for review (draft → pending)
"""
import uuid

from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Episode, Season, Show, Video
from apps.cms import cloudflare
from .permissions import IsCreator
from .serializers import (StudioEpisodeSerializer, StudioSeasonSerializer,
                          StudioShowSerializer)


def _own_show(user, show_id):
    """Fetch a show the user owns, or 404 (never leaks other creators' content)."""
    return get_object_or_404(Show, id=show_id, owner=user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enable(request):
    """Opt into creator mode. Idempotent."""
    if not request.user.is_creator:
        request.user.is_creator = True
        request.user.save(update_fields=["is_creator"])
    return Response({"ok": True, "is_creator": True})


class ShowsView(APIView):
    permission_classes = [IsCreator]

    def get(self, request):
        shows = (Show.objects.filter(owner=request.user)
                 .prefetch_related("seasons__episodes").order_by("-created_at"))
        return Response({"shows": StudioShowSerializer(shows, many=True).data})

    def post(self, request):
        instance = _own_show(request.user, request.data["id"]) if request.data.get("id") else None
        ser = StudioShowSerializer(instance, data=request.data, partial=bool(instance))
        ser.is_valid(raise_exception=True)
        extra = {}
        if not instance:
            base = slugify(request.data.get("title", "")) or "show"
            extra = {"owner": request.user, "slug": f"{base}-{uuid.uuid4().hex[:6]}"}
        return Response(StudioShowSerializer(ser.save(**extra)).data)


class SeasonsView(APIView):
    permission_classes = [IsCreator]

    def post(self, request):
        show = _own_show(request.user, request.data.get("show"))
        season, _ = Season.objects.get_or_create(
            show=show, number=int(request.data.get("number", 1)),
            defaults={"title": request.data.get("title", "")})
        return Response(StudioSeasonSerializer(season).data)


class EpisodesView(APIView):
    permission_classes = [IsCreator]

    def post(self, request):
        # The episode's season must belong to a show this creator owns.
        season = get_object_or_404(Season, id=request.data.get("season"), show__owner=request.user)
        instance = None
        if request.data.get("id"):
            instance = get_object_or_404(Episode, id=request.data["id"], season__show__owner=request.user)
        data = {**request.data, "season": season.id}
        ser = StudioEpisodeSerializer(instance, data=data, partial=bool(instance))
        ser.is_valid(raise_exception=True)
        return Response(StudioEpisodeSerializer(ser.save()).data)


class UploadURLView(APIView):
    permission_classes = [IsCreator]

    def post(self, request):
        result = cloudflare.create_direct_upload(
            max_seconds=int(request.data.get("max_seconds", 7200)))
        if not result.get("ok"):
            return Response(result, status=503)        # degrades until CF_* is set
        video = Video.objects.create(cf_stream_uid=result["uid"], ready=False)
        return Response({"ok": True, "uploadURL": result["uploadURL"],
                         "cf_uid": result["uid"], "video_id": str(video.id)})


@api_view(["POST"])
@permission_classes([IsCreator])
def submit(request):
    """Submit a show for moderation. Requires at least one episode with a video attached."""
    show = _own_show(request.user, request.data.get("show"))
    has_video = Episode.objects.filter(season__show=show, video__isnull=False).exists()
    if not has_video:
        return Response({"ok": False, "error": "no_episodes",
                         "detail": "add at least one episode with a video before submitting"},
                        status=400)
    show.status = "pending"
    show.save(update_fields=["status"])
    return Response({"ok": True, "id": str(show.id), "status": show.status})
