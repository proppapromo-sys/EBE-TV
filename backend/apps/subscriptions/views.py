from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing import stripe_client
from apps.billing.iap import verify_and_apply_iap
from .models import Plan, Subscription
from .serializers import PlanSerializer
from .services import invalidate_entitlement, subscription_summary

# Where IAP subscriptions are actually managed (the app can't cancel these server-side).
STORE_MANAGE_URL = {
    "apple": "https://apps.apple.com/account/subscriptions",
    "google": "https://play.google.com/store/account/subscriptions",
}


class PlansView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(active=True).order_by("price_cents")
        return Response({"plans": PlanSerializer(plans, many=True).data})


class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(subscription_summary(request.user.id))


class CancelSubscriptionView(APIView):
    """Clear, one-tap cancellation — the opposite of burying it. Cancels at period end so the
    member keeps what they paid for. IAP subs are managed in the store (we say so, with a link)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sub = (Subscription.objects.filter(user=request.user, status="active")
               .order_by("-current_period_end").first())
        if not sub:
            return Response({"ok": False, "error": "no_active_subscription"}, status=400)
        if sub.cancel_at_period_end:
            return Response({"ok": True, "already_canceling": True,
                             "ends_on": sub.current_period_end})

        if sub.source in STORE_MANAGE_URL:
            return Response({"ok": False, "error": "manage_in_store", "source": sub.source,
                             "manage_url": STORE_MANAGE_URL[sub.source],
                             "detail": f"{sub.source.title()} subscriptions are canceled in the "
                                       f"{'App Store' if sub.source == 'apple' else 'Play Store'}."},
                            status=409)

        # Stripe (web): cancel at period end; webhook will confirm, but reflect it now too.
        if stripe_client.configured() and sub.external_id:
            res = stripe_client.cancel_subscription(sub.external_id, at_period_end=True)
            if not res.get("ok"):
                return Response(res, status=502)
        sub.cancel_at_period_end = True
        sub.updated_at = timezone.now()
        sub.save(update_fields=["cancel_at_period_end", "updated_at"])
        invalidate_entitlement(request.user.id)
        return Response({"ok": True, "ends_on": sub.current_period_end})


class SubscribeStripeView(APIView):
    """Web checkout: create a Stripe Checkout Session for the chosen plan."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan = Plan.objects.filter(code=request.data.get("plan_code"), active=True).first()
        if not plan:
            return Response({"error": "unknown_plan"}, status=400)
        result = stripe_client.create_checkout_session(request.user, plan)
        code = 200 if result.get("ok") else 400
        return Response(result, status=code)


class VerifyIAPView(APIView):
    """iOS/Android: the app posts its signed transaction / purchaseToken; we verify with the
    provider and normalize into a Subscription row."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        result = verify_and_apply_iap(
            user=request.user,
            platform=request.data.get("platform"),     # 'apple' | 'google'
            payload=request.data,
        )
        return Response(result, status=200 if result.get("ok") else 400)
