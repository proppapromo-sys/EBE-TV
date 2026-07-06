"""
Creator-facing payout API (all require auth — these are the logged-in creator's own money).

  POST /api/creator/onboard   → create/reuse a Connect account + return a hosted onboarding link
  GET  /api/creator/account   → onboarding/payout status (refreshed from Stripe when configured)
  GET  /api/creator/earnings  → this creator's earnings ledger across periods
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import connect, services
from .models import CreatorAccount, CreatorEarning
from .serializers import CreatorAccountSerializer, CreatorEarningSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def onboard(request):
    """Start (or resume) Stripe Connect onboarding for the current user."""
    account, _ = CreatorAccount.objects.get_or_create(user=request.user)

    if not account.stripe_account_id:
        created = connect.create_account(request.user)
        if not created.get("ok"):
            return Response(created, status=503)
        account.stripe_account_id = created["account_id"]
        account.save(update_fields=["stripe_account_id", "updated_at"])

    link = connect.create_onboarding_link(account.stripe_account_id)
    if not link.get("ok"):
        return Response(link, status=503)
    return Response({"ok": True, "onboarding_url": link["url"],
                     "account": CreatorAccountSerializer(account).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def account(request):
    """Return the creator account, refreshing payout-readiness from Stripe when configured."""
    account = CreatorAccount.objects.filter(user=request.user).first()
    if not account:
        return Response({"ok": True, "onboarded": False, "account": None})
    if account.stripe_account_id and connect.configured():
        services.refresh_account(account)
    return Response({"ok": True, "onboarded": account.can_receive,
                     "account": CreatorAccountSerializer(account).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def earnings(request):
    """The current creator's earnings ledger (most recent first)."""
    qs = (CreatorEarning.objects.filter(creator=request.user)
          .select_related("period").order_by("-period__period_start"))
    total_net = sum(e.net_cents for e in qs)
    return Response({"ok": True, "lifetime_net_cents": total_net,
                     "earnings": CreatorEarningSerializer(qs, many=True).data})
