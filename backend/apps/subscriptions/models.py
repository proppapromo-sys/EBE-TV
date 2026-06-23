import uuid

from django.conf import settings
from django.db import models

ACTIVE, PAST_DUE, CANCELED, EXPIRED = "active", "past_due", "canceled", "expired"
STATUS_CHOICES = [(s, s) for s in (ACTIVE, PAST_DUE, CANCELED, EXPIRED)]
SOURCES = [(s, s) for s in ("stripe", "apple", "google")]


class Plan(models.Model):
    """Single all-access tier, two billing intervals (monthly / annual)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)        # 'monthly' | 'annual'
    interval = models.CharField(max_length=10)                 # 'month' | 'year'
    price_cents = models.IntegerField()
    currency = models.CharField(max_length=3, default="usd")
    stripe_price_id = models.CharField(max_length=120, blank=True)
    apple_product_id = models.CharField(max_length=120, blank=True)
    google_product_id = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} ({self.price_cents/100:.2f} {self.currency}/{self.interval})"


class Subscription(models.Model):
    """The entitlement source of truth. All three billing sources normalize into this row."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="subscriptions",
                             on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES)
    source = models.CharField(max_length=10, choices=SOURCES)
    external_id = models.CharField(max_length=200, blank=True)   # provider subscription id
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user", "status", "current_period_end"])]
        unique_together = ("source", "external_id")
