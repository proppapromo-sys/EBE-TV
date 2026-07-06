"""
The entitlement gate — the single function the whole platform trusts to answer "may this user
play?". Backed by a 5-minute Redis cache; every billing change busts it immediately so access
flips the moment a subscription starts, lapses, or is canceled.
"""
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .models import Subscription


def _key(user_id):
    return f"sub:{user_id}"


def is_entitled(user_id) -> bool:
    cached = cache.get(_key(user_id))
    if cached is not None:
        return cached
    sub = (Subscription.objects
           .filter(user_id=user_id, status="active")
           .order_by("-current_period_end")
           .first())
    entitled = bool(sub and sub.current_period_end and sub.current_period_end > timezone.now())
    cache.set(_key(user_id), entitled, timeout=settings.ENTITLEMENT_CACHE_TTL)
    return entitled


def invalidate_entitlement(user_id):
    """Call from every billing webhook/verify on any subscription change."""
    cache.delete(_key(user_id))


def subscription_summary(user_id) -> dict:
    sub = (Subscription.objects
           .filter(user_id=user_id)
           .order_by("-current_period_end")
           .first())
    if not sub:
        return {"entitled": False, "status": "none", "plan": None}
    return {
        "entitled": is_entitled(user_id),
        "status": sub.status,
        "source": sub.source,
        "plan": sub.plan.code if sub.plan else None,
        "current_period_end": sub.current_period_end,
        "cancel_at_period_end": sub.cancel_at_period_end,
    }
