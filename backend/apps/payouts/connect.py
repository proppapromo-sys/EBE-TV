"""
Stripe Connect — creator onboarding + transfers. Same fail-closed contract as billing/stripe_client:
returns {"ok": False, "error": "stripe_not_configured"} until STRIPE_SECRET_KEY is set, so the rest
of the payout pipeline (earnings math, ledgers, admin) runs with zero configuration.
"""
from django.conf import settings

try:
    import stripe
except ImportError:                     # dependency optional at import time
    stripe = None


def configured() -> bool:
    return bool(stripe and settings.STRIPE_SECRET_KEY)


def _client():
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_account(user) -> dict:
    """Create an Express connected account for a creator (idempotent caller passes existing id)."""
    if not configured():
        return {"ok": False, "error": "stripe_not_configured",
                "detail": "set STRIPE_SECRET_KEY to enable creator payouts"}
    acct = _client().Account.create(
        type="express",
        email=user.email,
        capabilities={"transfers": {"requested": True}},
        business_type="individual",
        metadata={"user_id": str(user.id)},
    )
    return {"ok": True, "account_id": acct.id}


def create_onboarding_link(account_id) -> dict:
    """A one-time hosted link the creator opens to submit KYC / bank details."""
    if not configured():
        return {"ok": False, "error": "stripe_not_configured"}
    link = _client().AccountLink.create(
        account=account_id,
        refresh_url=settings.STRIPE_CONNECT_REFRESH_URL,
        return_url=settings.STRIPE_CONNECT_RETURN_URL,
        type="account_onboarding",
    )
    return {"ok": True, "url": link.url, "expires_at": link.expires_at}


def account_status(account_id) -> dict:
    """Poll Stripe for onboarding/payout readiness (refresh our CreatorAccount flags from this)."""
    if not configured():
        return {"ok": False, "error": "stripe_not_configured"}
    a = _client().Account.retrieve(account_id)
    return {"ok": True,
            "details_submitted": bool(a.get("details_submitted")),
            "charges_enabled": bool(a.get("charges_enabled")),
            "payouts_enabled": bool(a.get("payouts_enabled"))}


def create_transfer(account_id, amount_cents, currency, idempotency_key, metadata=None) -> dict:
    """Move `amount_cents` from the platform balance to the creator's connected account."""
    if not configured():
        return {"ok": False, "error": "stripe_not_configured"}
    try:
        tr = _client().Transfer.create(
            amount=int(amount_cents),
            currency=currency,
            destination=account_id,
            metadata=metadata or {},
            idempotency_key=idempotency_key,
        )
        return {"ok": True, "transfer_id": tr.id}
    except Exception as e:                      # surfaced to the ledger as a failed earning
        return {"ok": False, "error": "transfer_failed", "detail": str(e)}
