"""
Creator payouts — the money path for people who stream their own shows here.

Three tables mirror the three steps:
  CreatorAccount  → who can be paid (Stripe Connect onboarding state).
  PayoutPeriod    → a revenue window to distribute (the subscription pool for, say, a month).
  CreatorEarning  → what each creator earned that period (watch-time pro-rata) and its transfer.

Earnings are computed off `catalog.WatchProgress` (watch-time pro-rata) and paid out via
Stripe Connect transfers. Like the rest of billing, every external call degrades gracefully when
keys are absent, so the model + math run with zero configuration.
"""
import uuid

from django.conf import settings
from django.db import models

# CreatorEarning lifecycle
PENDING, PAID, FAILED, SKIPPED = "pending", "paid", "failed", "skipped"
EARNING_STATUS = [(s, s) for s in (PENDING, PAID, FAILED, SKIPPED)]

# PayoutPeriod lifecycle
OPEN, COMPUTED, PAID_OUT = "open", "computed", "paid_out"
PERIOD_STATUS = [(s, s) for s in (OPEN, COMPUTED, PAID_OUT)]


class CreatorAccount(models.Model):
    """A creator's Stripe Connect (Express) account. `payouts_enabled` gates real transfers."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="creator_account",
                                on_delete=models.CASCADE)
    stripe_account_id = models.CharField(max_length=120, blank=True)   # acct_xxx
    details_submitted = models.BooleanField(default=False)             # finished onboarding form
    charges_enabled = models.BooleanField(default=False)
    payouts_enabled = models.BooleanField(default=False)               # cleared to receive money
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def can_receive(self) -> bool:
        return bool(self.stripe_account_id and self.payouts_enabled)

    def __str__(self):
        return f"{self.user} → {self.stripe_account_id or '(no account)'}"


class PayoutPeriod(models.Model):
    """A revenue window to distribute. `revenue_pool_cents` is the money split across creators
    for [period_start, period_end); `platform_fee_bps` is the cut the platform keeps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    revenue_pool_cents = models.BigIntegerField(default=0)
    platform_fee_bps = models.IntegerField(default=3000)   # 30% (basis points: 10000 = 100%)
    currency = models.CharField(max_length=3, default="usd")
    status = models.CharField(max_length=12, choices=PERIOD_STATUS, default=OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start"]
        indexes = [models.Index(fields=["status", "period_start"])]

    def __str__(self):
        return f"{self.period_start:%Y-%m-%d}..{self.period_end:%Y-%m-%d} ({self.status})"


class CreatorEarning(models.Model):
    """One creator's slice of one period. Idempotent on (period, creator)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.ForeignKey(PayoutPeriod, related_name="earnings", on_delete=models.CASCADE)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="earnings",
                                on_delete=models.CASCADE)
    watched_seconds = models.BigIntegerField(default=0)
    share_bps = models.IntegerField(default=0)        # creator's fraction of the pool, basis points
    gross_cents = models.BigIntegerField(default=0)   # pool * share
    fee_cents = models.BigIntegerField(default=0)     # platform cut
    net_cents = models.BigIntegerField(default=0)     # payable to creator
    status = models.CharField(max_length=12, choices=EARNING_STATUS, default=PENDING)
    stripe_transfer_id = models.CharField(max_length=120, blank=True)
    detail = models.CharField(max_length=300, blank=True)   # failure / skip reason
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("period", "creator")
        indexes = [models.Index(fields=["period", "status"])]

    def __str__(self):
        return f"{self.creator}: {self.net_cents/100:.2f} ({self.status})"
