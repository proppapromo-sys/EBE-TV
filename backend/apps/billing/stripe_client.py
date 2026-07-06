"""Stripe — web checkout + webhook handling. Full margin (no app-store cut)."""
from datetime import datetime, timezone as tz

from django.conf import settings

from .normalize import apply_subscription_state

try:
    import stripe
except ImportError:                     # dependency optional at import time
    stripe = None


def configured() -> bool:
    return bool(stripe and settings.STRIPE_SECRET_KEY)


def _client():
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_checkout_session(user, plan) -> dict:
    if not configured():
        return {"ok": False, "error": "stripe_not_configured",
                "detail": "set STRIPE_SECRET_KEY (and STRIPE_PRICE_* on plans)"}
    price_id = plan.stripe_price_id or (
        settings.STRIPE_PRICE_MONTHLY if plan.code == "monthly" else settings.STRIPE_PRICE_ANNUAL)
    if not price_id:
        return {"ok": False, "error": "missing_stripe_price",
                "detail": "set the plan's stripe_price_id or STRIPE_PRICE_%s" % plan.code.upper()}
    s = _client().checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.CHECKOUT_SUCCESS_URL,
        cancel_url=settings.CHECKOUT_CANCEL_URL,
        client_reference_id=str(user.id),
        customer_email=user.email,
        metadata={"user_id": str(user.id), "plan_code": plan.code},
        subscription_data={"metadata": {"user_id": str(user.id), "plan_code": plan.code}},
    )
    return {"ok": True, "checkout_url": s.url, "session_id": s.id}


def cancel_subscription(external_id, at_period_end=True) -> dict:
    """Cancel a Stripe subscription. Default cancels at period end (keep access until paid-through);
    the customer.subscription.updated webhook then normalizes cancel_at_period_end back to us."""
    if not configured():
        return {"ok": False, "error": "stripe_not_configured"}
    try:
        _client().Subscription.modify(external_id, cancel_at_period_end=at_period_end)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": "stripe_error", "detail": str(e)}


def _ts(epoch):
    return datetime.fromtimestamp(epoch, tz=tz.utc) if epoch else None


def handle_event(event) -> dict:
    """Map Stripe subscription lifecycle events onto our normalized subscription state."""
    typ = event["type"]
    obj = event["data"]["object"]
    meta = obj.get("metadata") or {}
    user_id = meta.get("user_id") or (obj.get("subscription_details") or {}).get("metadata", {}).get("user_id")
    plan_code = meta.get("plan_code")

    if typ == "checkout.session.completed":
        return _norm(meta.get("user_id"), obj.get("subscription"), plan_code, "active",
                     _ts(obj.get("expires_at")))
    if typ in ("customer.subscription.created", "customer.subscription.updated", "invoice.paid"):
        sub = obj if obj.get("object") == "subscription" else None
        ext = (sub or {}).get("id") or obj.get("subscription")
        status_map = {"active": "active", "trialing": "active", "past_due": "past_due",
                      "canceled": "canceled", "unpaid": "past_due"}
        status = status_map.get((sub or {}).get("status", "active"), "active")
        return _norm(user_id, ext, plan_code, status,
                     _ts((sub or {}).get("current_period_end") or obj.get("period_end")),
                     bool((sub or {}).get("cancel_at_period_end")))
    if typ == "customer.subscription.deleted":
        return _norm(user_id, obj.get("id"), plan_code, "canceled",
                     _ts(obj.get("current_period_end")))
    return {"ok": True, "ignored": typ}


def _norm(user_id, external_id, plan_code, status, period_end, cancel_at_end=False):
    if not user_id or not external_id:
        return {"ok": True, "ignored": "missing user_id/external_id in metadata"}
    apply_subscription_state(user_id, "stripe", external_id, plan_code, status,
                             period_end, cancel_at_end)
    return {"ok": True, "applied": status}
