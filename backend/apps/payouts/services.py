"""
Attribution + payout services.

`compute_earnings` is the heart: it splits a period's revenue pool across creators by **watch-time
pro-rata** — each creator's share = (seconds watched of their shows) / (total seconds watched of all
owned shows) in the window. We read that signal from `catalog.WatchProgress` (position_s, updated in
window). A production system would feed this off playback heartbeat events for true cumulative watch
time; WatchProgress is the same shape and a faithful proxy for the foundation.

`run_payouts` is the executor: for each computed earning with a payable balance and a payout-ready
creator account, it issues a Stripe Connect transfer (idempotent per earning) and records the result.
"""
from django.db.models import Sum
from django.utils import timezone

from apps.catalog.models import WatchProgress

from . import connect
from .models import (COMPUTED, FAILED, PAID, PAID_OUT, PENDING, SKIPPED,
                     CreatorAccount, CreatorEarning)


def compute_earnings(period) -> dict:
    """Materialize CreatorEarning rows for `period` from watch-time pro-rata. Idempotent."""
    rows = (WatchProgress.objects
            .filter(updated_at__gte=period.period_start,
                    updated_at__lt=period.period_end,
                    episode__season__show__owner__isnull=False)
            .values("episode__season__show__owner")
            .annotate(seconds=Sum("position_s")))

    by_creator = {r["episode__season__show__owner"]: int(r["seconds"] or 0)
                  for r in rows if (r["seconds"] or 0) > 0}
    total = sum(by_creator.values())
    pool = int(period.revenue_pool_cents)
    fee_bps = int(period.platform_fee_bps)

    results = []
    for creator_id, seconds in by_creator.items():
        # Fixed-point share so the pool is split exactly without float drift.
        gross = pool * seconds // total if total else 0
        share_bps = seconds * 10000 // total if total else 0
        fee = gross * fee_bps // 10000
        net = gross - fee
        earning, _ = CreatorEarning.objects.update_or_create(
            period=period, creator_id=creator_id,
            defaults={"watched_seconds": seconds, "share_bps": share_bps,
                      "gross_cents": gross, "fee_cents": fee, "net_cents": net,
                      "status": PENDING, "detail": ""},
        )
        results.append(earning)

    period.status = COMPUTED
    period.save(update_fields=["status"])
    return {"ok": True, "creators": len(results), "total_seconds": total,
            "distributed_cents": sum(e.gross_cents for e in results)}


def run_payouts(period, *, live=True) -> dict:
    """Issue Stripe transfers for every pending, payable earning in `period`. Idempotent per row."""
    paid = skipped = failed = 0
    for e in period.earnings.filter(status=PENDING):
        if e.net_cents <= 0:
            _mark(e, SKIPPED, "zero_balance")
            skipped += 1
            continue
        acct = CreatorAccount.objects.filter(user_id=e.creator_id).first()
        if not acct or not acct.can_receive:
            _mark(e, SKIPPED, "creator_not_onboarded")
            skipped += 1
            continue
        if not live or not connect.configured():
            _mark(e, SKIPPED, "stripe_not_configured")
            skipped += 1
            continue
        res = connect.create_transfer(
            acct.stripe_account_id, e.net_cents, period.currency,
            idempotency_key=f"payout-{e.id}",
            metadata={"period_id": str(period.id), "creator_id": str(e.creator_id)})
        if res.get("ok"):
            e.stripe_transfer_id = res["transfer_id"]
            _mark(e, PAID, "")
            paid += 1
        else:
            _mark(e, FAILED, res.get("detail") or res.get("error", "transfer_failed"))
            failed += 1

    if failed == 0:
        period.status = PAID_OUT
        period.save(update_fields=["status"])
    return {"ok": True, "paid": paid, "skipped": skipped, "failed": failed}


def _mark(earning, status, detail):
    earning.status = status
    earning.detail = detail
    earning.updated_at = timezone.now()
    earning.save(update_fields=["status", "detail", "stripe_transfer_id", "updated_at"])


def refresh_account(account: CreatorAccount) -> dict:
    """Sync our CreatorAccount flags from Stripe (call after onboarding return)."""
    if not account.stripe_account_id:
        return {"ok": False, "error": "no_account"}
    st = connect.account_status(account.stripe_account_id)
    if not st.get("ok"):
        return st
    account.details_submitted = st["details_submitted"]
    account.charges_enabled = st["charges_enabled"]
    account.payouts_enabled = st["payouts_enabled"]
    account.save(update_fields=["details_submitted", "charges_enabled",
                                "payouts_enabled", "updated_at"])
    return {"ok": True, "payouts_enabled": account.payouts_enabled}
