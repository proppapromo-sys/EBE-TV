from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Episode, WatchProgress
from apps.subscriptions.services import is_entitled
from . import cloudflare


class PlayView(APIView):
    """THE GATE: entitlement check → short-lived signed playback token. The only place a client
    ever learns how to fetch a manifest; raw video URLs are never exposed elsewhere."""
    permission_classes = [IsAuthenticated]

    def get(self, request, episode_id):
        if not is_entitled(request.user.id):
            return Response({"error": "subscription_required"}, status=403)

        episode = get_object_or_404(Episode, id=episode_id, status="published")
        video = episode.video
        if not video or not video.ready:
            return Response({"error": "not_available"}, status=404)

        if not cloudflare.configured():
            return Response({"error": "playback_not_configured",
                             "detail": "set CF_STREAM_SIGNING_KEY_ID / CF_STREAM_SIGNING_KEY_PEM "
                                       "and CF_CUSTOMER_SUBDOMAIN"}, status=503)

        token = cloudflare.signed_token(video.cf_stream_uid, user_id=request.user.id)
        progress = (WatchProgress.objects
                    .filter(user=request.user, episode=episode)
                    .values_list("position_s", flat=True).first())
        captions = [{"language": c.language, "label": c.label or c.language.upper()}
                    for c in video.captions.filter(ready=True)]
        return Response({
            "type": "dash",
            "playback_token": token,
            "manifest": cloudflare.manifests(token),
            "captions": captions,
            "expires_in": settings.PLAYBACK_TOKEN_TTL,
            "resume_position_s": progress or 0,
        })


class ProgressView(APIView):
    """Save continue-watching position (heartbeat from the player)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, episode_id):
        episode = get_object_or_404(Episode, id=episode_id)
        try:
            position = int(request.data.get("position_s", 0))
        except (TypeError, ValueError):
            return Response({"error": "bad_position"}, status=400)
        WatchProgress.objects.update_or_create(
            user=request.user, episode=episode, defaults={"position_s": max(0, position)})
        return Response({"ok": True})
