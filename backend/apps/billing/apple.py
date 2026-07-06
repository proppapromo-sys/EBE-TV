"""
Apple — StoreKit 2 verification + App Store Server Notifications v2.

Wiring checklist (replace the stub bodies):
  • verify_and_apply: call the App Store Server API `Get Transaction Info`
    (https://api.storekit.itunes.apple.com/inApps/v1/transactions/{transactionId}), authed with a
    JWT signed by your APPLE_PRIVATE_KEY (.p8) / APPLE_KEY_ID / APPLE_ISSUER_ID. Decode the signed
    JWS transaction, map productId -> plan_code, expiresDate -> period_end.
  • handle_notification: App Store Server Notifications v2 arrive as a signed JWS payload. Verify
    the x5c certificate chain up to Apple's root, then map notificationType:
      SUBSCRIBED / DID_RENEW            -> active   (extend period)
      DID_FAIL_TO_RENEW (grace)         -> past_due
      EXPIRED                           -> expired
      REFUND                            -> canceled
"""
from django.conf import settings

from .normalize import apply_subscription_state          # noqa: F401 (used once wired)

_NOTIF_STATUS = {
    "SUBSCRIBED": "active", "DID_RENEW": "active",
    "DID_FAIL_TO_RENEW": "past_due", "GRACE_PERIOD_EXPIRED": "past_due",
    "EXPIRED": "expired", "REFUND": "canceled", "REVOKE": "canceled",
}


def apple_configured() -> bool:
    return bool(settings.APPLE_KEY_ID and settings.APPLE_PRIVATE_KEY and settings.APPLE_ISSUER_ID)


def verify_and_apply(user, payload) -> dict:
    if not apple_configured():
        return {"ok": False, "error": "apple_not_configured",
                "detail": "set APPLE_ISSUER_ID / APPLE_KEY_ID / APPLE_PRIVATE_KEY / APPLE_BUNDLE_ID"}
    # TODO: verify payload['signedTransaction'] with the App Store Server API, then:
    # apply_subscription_state(user.id, "apple", transaction_id, plan_code, "active", expires_date)
    return {"ok": False, "error": "not_implemented",
            "detail": "verify the StoreKit2 signed transaction, then call apply_subscription_state"}


def handle_notification(signed_payload) -> dict:
    if not apple_configured():
        return {"ok": True, "ignored": "apple_not_configured"}
    # TODO: verify JWS cert chain, decode, map notificationType via _NOTIF_STATUS, normalize.
    return {"ok": True, "ignored": "stub"}
