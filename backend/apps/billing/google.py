"""
Google Play — purchase verification + Real-time Developer Notifications (RTDN via Pub/Sub push).

Wiring checklist (replace the stub bodies):
  • verify_and_apply: call the Google Play Developer API
    `purchases.subscriptionsv2.get` with GOOGLE_SERVICE_ACCOUNT_JSON for the package
    GOOGLE_PACKAGE_NAME and the app-supplied purchaseToken. Map the line item's productId ->
    plan_code and expiryTime -> period_end; acknowledge the purchase.
  • handle_notification: RTDN arrives base64-encoded in a Pub/Sub envelope
    (message.data). Decode the JSON, read subscriptionNotification.notificationType:
      4 SUBSCRIPTION_PURCHASED / 2 RENEWED        -> active
      3 CANCELED                                  -> canceled
      13 EXPIRED                                  -> expired
      6 IN_GRACE_PERIOD                           -> past_due
"""
import base64
import json

from django.conf import settings

from .normalize import apply_subscription_state          # noqa: F401 (used once wired)

_RTDN_STATUS = {2: "active", 4: "active", 1: "past_due", 6: "past_due",
                3: "canceled", 12: "canceled", 13: "expired", 5: "expired"}


def google_configured() -> bool:
    return bool(settings.GOOGLE_SERVICE_ACCOUNT_JSON and settings.GOOGLE_PACKAGE_NAME)


def verify_and_apply(user, payload) -> dict:
    if not google_configured():
        return {"ok": False, "error": "google_not_configured",
                "detail": "set GOOGLE_SERVICE_ACCOUNT_JSON / GOOGLE_PACKAGE_NAME"}
    # TODO: verify payload['purchaseToken'] via purchases.subscriptionsv2.get, then:
    # apply_subscription_state(user.id, "google", purchase_token, plan_code, "active", expiry)
    return {"ok": False, "error": "not_implemented",
            "detail": "verify the purchaseToken with the Play Developer API, then normalize"}


def handle_notification(envelope) -> dict:
    """Decode the Pub/Sub push envelope. Returns the parsed RTDN (verification still TODO)."""
    try:
        data = json.loads(base64.b64decode(envelope["message"]["data"]).decode())
    except Exception:
        return {"ok": False, "error": "bad_envelope"}
    if not google_configured():
        return {"ok": True, "ignored": "google_not_configured", "rtdn": data}
    # TODO: look up purchaseToken -> user, map notificationType via _RTDN_STATUS, normalize.
    return {"ok": True, "ignored": "stub", "rtdn": data}
