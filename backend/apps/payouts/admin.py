from django.contrib import admin

from .models import CreatorAccount, CreatorEarning, PayoutPeriod


@admin.register(CreatorAccount)
class CreatorAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "stripe_account_id", "details_submitted",
                    "payouts_enabled", "updated_at")
    list_filter = ("payouts_enabled", "details_submitted")
    search_fields = ("user__email", "stripe_account_id")


class CreatorEarningInline(admin.TabularInline):
    model = CreatorEarning
    extra = 0
    readonly_fields = ("creator", "watched_seconds", "share_bps", "gross_cents",
                       "fee_cents", "net_cents", "status", "stripe_transfer_id", "detail")
    can_delete = False


@admin.register(PayoutPeriod)
class PayoutPeriodAdmin(admin.ModelAdmin):
    list_display = ("period_start", "period_end", "revenue_pool_cents",
                    "platform_fee_bps", "status", "created_at")
    list_filter = ("status",)
    inlines = [CreatorEarningInline]


@admin.register(CreatorEarning)
class CreatorEarningAdmin(admin.ModelAdmin):
    list_display = ("creator", "period", "net_cents", "status", "stripe_transfer_id")
    list_filter = ("status",)
    search_fields = ("creator__email", "stripe_transfer_id")
