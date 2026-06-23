"""
The normalizer — the single choke point where Stripe, Apple, and Google all write the SAME
subscription state. Every webhook/verify path ends here, and every change busts the entitlement
cache so access flips immediately. Idempotent: update_or_create keyed on (source, external_id).
"""
from django.utils import timezone

from apps.subscriptions.models import Plan, Subscription
from apps.subscriptions.services import invalidate_entitlement


def apply_subscription_state(user_id, source, external_id, plan_code, status,
                             period_end, cancel_at_end=False):
    plan = Plan.objects.filter(code=plan_code).first() if plan_code else None
    sub, _ = Subscription.objects.update_or_create(
        source=source, external_id=external_id,
        defaults={
            "user_id": user_id,
            "plan": plan,
            "status": status,
            "current_period_end": period_end,
            "cancel_at_period_end": cancel_at_end,
            "updated_at": timezone.now(),
        },
    )
    invalidate_entitlement(user_id)
    return sub
