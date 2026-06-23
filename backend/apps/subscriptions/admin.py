from django.contrib import admin

from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "interval", "price_cents", "currency", "active")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "source", "plan", "current_period_end",
                    "cancel_at_period_end")
    list_filter = ("status", "source")
    search_fields = ("user__email", "external_id")
