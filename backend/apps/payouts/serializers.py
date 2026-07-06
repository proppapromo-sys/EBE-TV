from rest_framework import serializers

from .models import CreatorAccount, CreatorEarning


class CreatorAccountSerializer(serializers.ModelSerializer):
    can_receive = serializers.BooleanField(read_only=True)

    class Meta:
        model = CreatorAccount
        fields = ("stripe_account_id", "details_submitted", "charges_enabled",
                  "payouts_enabled", "can_receive", "created_at", "updated_at")


class CreatorEarningSerializer(serializers.ModelSerializer):
    period_start = serializers.DateTimeField(source="period.period_start", read_only=True)
    period_end = serializers.DateTimeField(source="period.period_end", read_only=True)
    currency = serializers.CharField(source="period.currency", read_only=True)

    class Meta:
        model = CreatorEarning
        fields = ("id", "period_start", "period_end", "currency", "watched_seconds",
                  "share_bps", "gross_cents", "fee_cents", "net_cents", "status",
                  "stripe_transfer_id", "detail", "updated_at")
