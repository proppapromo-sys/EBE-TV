"""Seed demo data so the API + web client have something to show immediately.

    python manage.py seed_demo
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.catalog.models import (Collection, CollectionItem, Episode, Season,
                                 Show, Video)
from apps.subscriptions.models import Plan, Subscription

User = get_user_model()

# Original EBE-TV demo catalog — invented placeholder titles + EBE's own editorial rows.
SHOWS = {
    "midnight-bloom": ("Midnight Bloom", ["Drama"]),
    "crown-city": ("Crown City", ["Reality"]),
    "the-come-up": ("The Come Up", ["Docuseries"]),
    "last-call": ("Last Call", ["Reality"]),
    "paper-chase": ("Paper Chase", ["Drama"]),
    "off-the-record": ("Off the Record", ["Talk"]),
    "glow-up": ("Glow Up", ["Reality"]),
    "block-party": ("Block Party", ["Music"]),
    "two-truths": ("Two Truths", ["Reality"]),
    "after-hours": ("After Hours", ["Late Night"]),
    "heatwave": ("Heatwave", ["Event"]),
    "spotlight-sessions": ("Spotlight Sessions", ["Showcase"]),
}
ROWS = [
    ("Tonight on EBE", "tonight", "hero", ["midnight-bloom", "crown-city", "the-come-up"]),
    ("Fresh Drops", "fresh-drops", "row", ["heatwave", "glow-up", "after-hours"]),
    ("EBE Originals", "ebe-originals", "row", ["midnight-bloom", "paper-chase", "two-truths"]),
    ("Binge-Worthy", "binge-worthy", "row", ["crown-city", "last-call", "block-party"]),
    ("Live & Loud", "live-loud", "row", ["spotlight-sessions", "heatwave", "off-the-record"]),
]


class Command(BaseCommand):
    help = "Create demo plans, a curated catalog of shows + browse rows, and a subscribed user."

    def handle(self, *args, **opts):
        Plan.objects.get_or_create(code="monthly", defaults=dict(
            interval="month", price_cents=999, stripe_price_id=""))
        Plan.objects.get_or_create(code="annual", defaults=dict(
            interval="year", price_cents=9999, stripe_price_id=""))

        # Shows (each published, with poster/hero art and a few episodes).
        shows = {}
        for slug, (title, genre) in SHOWS.items():
            show, _ = Show.objects.get_or_create(slug=slug, defaults=dict(
                title=title, status="published",
                description=f"{title} — a sample show seeded for local development.",
                poster_url=f"https://picsum.photos/seed/{slug}/400/600",
                hero_url=f"https://picsum.photos/seed/{slug}-hero/1280/520",
                genre=genre))
            shows[slug] = show
            season, _ = Season.objects.get_or_create(show=show, number=1,
                                                     defaults={"title": "Season 1"})
            for i in range(1, 4):
                if Episode.objects.filter(season=season, number=i).exists():
                    continue
                video = Video.objects.create(cf_stream_uid=f"{slug}-uid-{i}", ready=True,
                                             duration_s=1800)
                Episode.objects.create(season=season, number=i, title=f"Episode {i}",
                                       description="Seeded episode.", status="published",
                                       published_at=timezone.now(), duration_s=1800, video=video,
                                       thumbnail_url=f"https://picsum.photos/seed/{slug}{i}/320/180")

        # Curated browse rows.
        for pos, (title, slug, kind, members) in enumerate(ROWS):
            col, _ = Collection.objects.get_or_create(slug=slug, defaults=dict(
                title=title, kind=kind, position=pos, published=True))
            for ipos, member in enumerate(members):
                if member in shows:
                    CollectionItem.objects.get_or_create(
                        collection=col, show=shows[member], defaults={"position": ipos})

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
