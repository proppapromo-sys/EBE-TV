from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models import Plan, Subscription
from apps.subscriptions.services import is_entitled, invalidate_entitlement

User = get_user_model()


class EntitlementGateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("v@test.com", "password123")
        self.plan = Plan.objects.create(code="monthly", interval="month", price_cents=999)

    def _sub(self, status, days):
        invalidate_entitlement(self.user.id)
        return Subscription.objects.create(
            user=self.user, plan=self.plan, source="stripe", external_id=f"e{status}{days}",
            status=status, current_period_end=timezone.now() + timedelta(days=days))

    def test_active_future_period_is_entitled(self):
        self._sub("active", 10)
        self.assertTrue(is_entitled(self.user.id))

    def test_active_but_expired_period_is_not_entitled(self):
        self._sub("active", -1)
        self.assertFalse(is_entitled(self.user.id))

    def test_canceled_is_not_entitled(self):
        self._sub("canceled", 10)
        self.assertFalse(is_entitled(self.user.id))

    def test_no_subscription_is_not_entitled(self):
        self.assertFalse(is_entitled(self.user.id))

    def test_cache_busts_on_change(self):
        self._sub("active", 10)
        self.assertTrue(is_entitled(self.user.id))
        Subscription.objects.filter(user=self.user).update(status="canceled")
        invalidate_entitlement(self.user.id)        # webhook would call this
        self.assertFalse(is_entitled(self.user.id))
