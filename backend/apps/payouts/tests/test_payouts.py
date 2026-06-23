"""
Watch-time pro-rata attribution + payout gating. Two creators, a 3:1 watch split, a 30% platform
fee — assert the pool divides correctly and that transfers are gated on onboarding.
"""
from datetime import datetime, timezone as tz

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Episode, Season, Show, WatchProgress
from apps.payouts.models import (CreatorAccount, CreatorEarning, PayoutPeriod,
                                 PAID, PENDING, SKIPPED)
from apps.payouts.services import compute_earnings, run_payouts

User = get_user_model()


def _episode(owner, title):
    show = Show.objects.create(title=title, slug=title.lower().replace(" ", "-"), owner=owner)
    season = Season.objects.create(show=show, number=1)
    return Episode.objects.create(season=season, number=1, title=f"{title} E1")


class PayoutAttributionTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice@test.test", "pw12345678")
        self.bob = User.objects.create_user("bob@test.test", "pw12345678")
        self.viewer = User.objects.create_user("viewer@test.test", "pw12345678")
        self.ep_a = _episode(self.alice, "Alice Show")
        self.ep_b = _episode(self.bob, "Bob Show")
        # 3:1 watch split — Alice 900s, Bob 300s (total 1200s).
        WatchProgress.objects.create(user=self.viewer, episode=self.ep_a, position_s=900)
        WatchProgress.objects.create(user=self.viewer, episode=self.ep_b, position_s=300)
        self.period = PayoutPeriod.objects.create(
            period_start=datetime(2026, 6, 1, tzinfo=tz.utc),
            period_end=datetime(2026, 7, 1, tzinfo=tz.utc),
            revenue_pool_cents=100_00, platform_fee_bps=3000)   # $100 pool, 30% fee

    def test_prorata_split_and_fee(self):
        res = compute_earnings(self.period)
        self.assertEqual(res["creators"], 2)

        alice = CreatorEarning.objects.get(period=self.period, creator=self.alice)
        bob = CreatorEarning.objects.get(period=self.period, creator=self.bob)

        # 75% / 25% of a $100 pool → gross $75 / $25; net after 30% fee → $52.50 / $17.50.
        self.assertEqual(alice.gross_cents, 7500)
        self.assertEqual(alice.fee_cents, 2250)
        self.assertEqual(alice.net_cents, 5250)
        self.assertEqual(alice.share_bps, 7500)
        self.assertEqual(bob.net_cents, 1750)

        # The whole pool is accounted for (gross sums to pool; nothing lost to rounding here).
        self.assertEqual(alice.gross_cents + bob.gross_cents, 10000)

    def test_unowned_watch_time_is_ignored(self):
        # A platform-owned show (owner=None) earns nobody a payout.
        ep_platform = Show.objects.create(title="Platform Original", slug="platform-original")
        season = Season.objects.create(show=ep_platform, number=1)
        ep = Episode.objects.create(season=season, number=1, title="PO E1")
        WatchProgress.objects.create(user=self.viewer, episode=ep, position_s=10_000)
        compute_earnings(self.period)
        # Alice still gets exactly 75% — platform watch time does not dilute the creator pool.
        alice = CreatorEarning.objects.get(period=self.period, creator=self.alice)
        self.assertEqual(alice.share_bps, 7500)

    def test_payout_gated_on_onboarding(self):
        compute_earnings(self.period)
        # No Connect account → skipped, not paid.
        res = run_payouts(self.period, live=False)
        self.assertEqual(res["paid"], 0)
        self.assertEqual(res["skipped"], 2)
        alice = CreatorEarning.objects.get(period=self.period, creator=self.alice)
        self.assertEqual(alice.status, SKIPPED)
        self.assertEqual(alice.detail, "creator_not_onboarded")

    def test_onboarded_creator_in_dry_run_is_not_charged(self):
        compute_earnings(self.period)
        CreatorAccount.objects.create(
            user=self.alice, stripe_account_id="acct_test", payouts_enabled=True)
        # Even onboarded, a non-live run records intent without moving money.
        res = run_payouts(self.period, live=False)
        self.assertEqual(res["paid"], 0)
        alice = CreatorEarning.objects.get(period=self.period, creator=self.alice)
        self.assertEqual(alice.status, SKIPPED)
        self.assertEqual(alice.detail, "stripe_not_configured")
