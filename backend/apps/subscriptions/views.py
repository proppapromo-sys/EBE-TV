from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing import stripe_client
from apps.billing.iap import verify_and_apply_iap
from .models import Plan
from .serializers import PlanSerializer
from .services import subscription_summary


class PlansView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(active=True).order_by("price_cents")
        return Response({"plans": PlanSerializer(plans, many=True).data})


class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(subscription_summary(request.user.id))


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
