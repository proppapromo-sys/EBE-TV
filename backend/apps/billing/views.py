import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import apple, google, stripe_client


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """Signature-verified Stripe events → normalized subscription state."""
    if not stripe_client.configured():
        return Response({"ok": True, "ignored": "stripe_not_configured"})
    import stripe
    sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(
            request.body, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return Response({"error": "invalid_signature", "detail": str(e)}, status=400)
    return Response(stripe_client.handle_event(event))


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def apple_webhook(request):
    """App Store Server Notifications v2 (signed JWS)."""
    try:
        body = json.loads(request.body or b"{}")
    except ValueError:
        body = {}
    return Response(apple.handle_notification(body.get("signedPayload")))


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def google_webhook(request):
    """Google RTDN via Pub/Sub push."""
    try:
        envelope = json.loads(request.body or b"{}")
    except ValueError:
        envelope = {}
    return Response(google.handle_notification(envelope))
