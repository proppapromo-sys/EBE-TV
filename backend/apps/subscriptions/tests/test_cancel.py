"""Discoverable cancellation: cancel-at-period-end for web, store redirect for IAP."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.subscriptions.models import Plan, Subscription

User = get_user_model()


class CancelSubscriptionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("viewer@test.test", "pw12345678")
        self.plan = Plan.objects.create(code="monthly", interval="month", price_cents=999)
        self.client.force_authenticate(self.user)

    def _sub(self, source="stripe", **kw):
        return Subscription.objects.create(
            user=self.user, plan=self.plan, status="active", source=source,
            external_id=f"{source}-1", current_period_end=timezone.now() + timedelta(days=10), **kw)

    def test_stripe_cancel_sets_cancel_at_period_end(self):
        self._sub("stripe")
        r = self.client.post("/api/subscribe/cancel")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["ok"])
        self.assertTrue(Subscription.objects.get(user=self.user).cancel_at_period_end)

    def test_cancel_keeps_access_until_period_end(self):
        # cancel_at_period_end must NOT immediately revoke entitlement.
        self._sub("stripe")
        self.client.post("/api/subscribe/cancel")
        me = self.client.get("/api/me")
        self.assertTrue(me.data["subscription"]["entitled"])
        self.assertTrue(me.data["subscription"]["cancel_at_period_end"])

    def test_iap_cancel_redirects_to_store(self):
        self._sub("apple")
        r = self.client.post("/api/subscribe/cancel")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data["error"], "manage_in_store")
        self.assertIn("apps.apple.com", r.data["manage_url"])

    def test_cancel_without_active_subscription(self):
        r = self.client.post("/api/subscribe/cancel")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"], "no_active_subscription")

    def test_cancel_is_idempotent(self):
        self._sub("stripe", cancel_at_period_end=True)
        r = self.client.post("/api/subscribe/cancel")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["already_canceling"])
