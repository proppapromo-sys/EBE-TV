from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Episode, Show, Video
from . import cloudflare
from .serializers import EpisodeWriteSerializer, ShowWriteSerializer


class UploadURLView(APIView):
    """Staff requests a Cloudflare direct-upload URL, then uploads the file straight to CF.
    We pre-create a Video row (not ready) keyed to the returned UID."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        result = cloudflare.create_direct_upload(
            max_seconds=int(request.data.get("max_seconds", 7200)))
        if not result.get("ok"):
            return Response(result, status=400)
        video = Video.objects.create(cf_stream_uid=result["uid"], ready=False)
        return Response({"ok": True, "uploadURL": result["uploadURL"],
                         "cf_uid": result["uid"], "video_id": str(video.id)})


class ShowsView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        instance = None
        if request.data.get("id"):
            instance = get_object_or_404(Show, id=request.data["id"])
        ser = ShowWriteSerializer(instance, data=request.data, partial=bool(instance))
        ser.is_valid(raise_exception=True)
        return Response(ShowWriteSerializer(ser.save()).data)


class EpisodesView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        instance = None
        if request.data.get("id"):
            instance = get_object_or_404(Episode, id=request.data["id"])
        ser = EpisodeWriteSerializer(instance, data=request.data, partial=bool(instance))
        ser.is_valid(raise_exception=True)
        return Response(EpisodeWriteSerializer(ser.save()).data)


class PublishView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        kind = request.data.get("kind")        # 'show' | 'episode'
        obj_id = request.data.get("id")
        if kind == "show":
            obj = get_object_or_404(Show, id=obj_id)
            obj.status = "published"
            obj.save(update_fields=["status"])
        elif kind == "episode":
            obj = get_object_or_404(Episode, id=obj_id)
            obj.status = "published"
            obj.published_at = timezone.now()
            obj.save(update_fields=["status", "published_at"])
        else:
            return Response({"error": "bad_kind"}, status=400)
        return Response({"ok": True, "id": obj_id, "status": "published"})


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def cf_transcode_webhook(request):
    """Cloudflare calls this when a video finishes transcoding → flip Video.ready = true.
    (Configure the webhook + verify its signature in production.)"""
    import json
    try:
        body = json.loads(request.body or b"{}")
    except ValueError:
        return Response({"error": "bad_json"}, status=400)
    uid = body.get("uid") or (body.get("data") or {}).get("uid")
    ready = ((body.get("status") or {}).get("state") == "ready") or body.get("readyToStream")
    if uid and ready:
        n = Video.objects.filter(cf_stream_uid=uid).update(
            ready=True, duration_s=int((body.get("duration") or 0)))
        return Response({"ok": True, "updated": n})
    return Response({"ok": True, "ignored": True})
