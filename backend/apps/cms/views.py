from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Episode, Show, Video
from . import cloudflare
from .ingest import ingest_manifest
from .serializers import EpisodeWriteSerializer, ShowWriteSerializer


class ModerationView(APIView):
    """Staff review queue: list submitted (pending) shows; approve (publish) or reject (→ draft)."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        shows = (Show.objects.filter(status="pending")
                 .select_related("owner").order_by("created_at"))
        out = [{
            "id": str(s.id), "title": s.title, "slug": s.slug,
            "owner_email": s.owner.email if s.owner else None,
            "episodes": Episode.objects.filter(season__show=s).count(),
            "ready_episodes": Episode.objects.filter(season__show=s, video__ready=True).count(),
        } for s in shows]
        return Response({"pending": out})

    def post(self, request):
        show = get_object_or_404(Show, id=request.data.get("id"))
        action = request.data.get("action")
        if action == "approve":
            show.status = "published"
            show.save(update_fields=["status"])
            # Publish episodes that have a ready video so the show is actually watchable.
            for ep in Episode.objects.filter(season__show=show, video__ready=True):
                ep.status = "published"
                ep.published_at = ep.published_at or timezone.now()
                ep.save(update_fields=["status", "published_at"])
        elif action == "reject":
            show.status = "draft"
            show.save(update_fields=["status"])
        else:
            return Response({"error": "bad_action"}, status=400)
        return Response({"ok": True, "id": str(show.id), "status": show.status})


class BulkIngestView(APIView):
    """Staff posts a manifest ({shows:[…], collections:[…]}) to load a library in one call."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        if not data.get("shows"):
            return Response({"ok": False, "error": "no_shows",
                             "detail": "body must be a manifest with a 'shows' array"}, status=400)
        summary = ingest_manifest(
            data,
            pull_video=data.get("pull_video", True),
            default_status="published" if data.get("publish") else "draft")
        return Response({"ok": True, **summary})


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
        # On create, default ownership to the uploader so they earn from it — unless an
        # explicit owner was supplied (admin assigning on a creator's behalf).
        extra = {} if (instance or request.data.get("owner")) else {"owner": request.user}
        return Response(ShowWriteSerializer(ser.save(**extra)).data)


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
    Signature-verified when CF_WEBHOOK_SECRET is set (set it + configure the webhook in prod)."""
    import json
    if not cloudflare.verify_webhook_signature(
            request.body, request.META.get("HTTP_WEBHOOK_SIGNATURE", "")):
        return Response({"error": "invalid_signature"}, status=403)
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
