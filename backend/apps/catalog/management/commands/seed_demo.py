"""Seed demo data so the API + web client have something to show immediately.

    python manage.py seed_demo
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.catalog.models import Episode, Season, Show, Video
from apps.subscriptions.models import Plan, Subscription

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo plans, a show with episodes, and a subscribed demo user."

    def handle(self, *args, **opts):
        Plan.objects.get_or_create(code="monthly", defaults=dict(
            interval="month", price_cents=999, stripe_price_id=""))
        Plan.objects.get_or_create(code="annual", defaults=dict(
            interval="year", price_cents=9999, stripe_price_id=""))

        show, _ = Show.objects.get_or_create(slug="demo-original", defaults=dict(
            title="Demo Original", status="published",
            description="A sample show seeded for local development.",
            poster_url="https://picsum.photos/seed/poster/400/600",
            hero_url="https://picsum.photos/seed/hero/1280/520",
            genre=["Drama", "Original"]))
        season, _ = Season.objects.get_or_create(show=show, number=1, defaults={"title": "Season 1"})
        for i in range(1, 4):
            video = Video.objects.create(cf_stream_uid=f"demo-uid-{i}", ready=True, duration_s=1800)
            Episode.objects.get_or_create(season=season, number=i, defaults=dict(
                title=f"Episode {i}", description="Seeded episode.", status="published",
                published_at=timezone.now(), duration_s=1800, video=video,
                thumbnail_url=f"https://picsum.photos/seed/ep{i}/320/180"))

        user, created = User.objects.get_or_create(email="demo@demo.test",
                                                   defaults={"display_name": "Demo Viewer"})
        if created:
            user.set_password("demopass123")
            user.save()
        Subscription.objects.update_or_create(
            source="stripe", external_id="demo-sub", defaults=dict(
                user=user, plan=Plan.objects.get(code="monthly"), status="active",
                current_period_end=timezone.now() + timedelta(days=30)))

        self.stdout.write(self.style.SUCCESS(
            "Seeded. Login: demo@demo.test / demopass123 (active subscription).\n"
            "Note: demo videos use fake Stream UIDs — /api/play returns a token only once "
            "Cloudflare keys are set and a real video is uploaded."))
