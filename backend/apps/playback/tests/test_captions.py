"""Captions surface in the play response (and ingest can declare them)."""
from datetime import timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.catalog.models import Caption, Episode, Season, Show, Video
from apps.subscriptions.models import Plan, Subscription

User = get_user_model()


def _rsa_pem():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(serialization.Encoding.PEM,
                             serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode()


@override_settings(CF_STREAM_SIGNING_KEY_ID="k1", CF_STREAM_SIGNING_KEY_PEM=_rsa_pem(),
                   CF_CUSTOMER_SUBDOMAIN="customer-x.cloudflarestream.com")
class CaptionPlaybackTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("v@ebe.tv", "pw12345678")
        plan = Plan.objects.create(code="monthly", interval="month", price_cents=999)
        Subscription.objects.create(user=self.user, plan=plan, status="active", source="stripe",
                                    external_id="s1",
                                    current_period_end=timezone.now() + timedelta(days=10))
        show = Show.objects.create(title="S", slug="s", status="published")
        season = Season.objects.create(show=show, number=1)
        self.video = Video.objects.create(cf_stream_uid="uid", ready=True)
        self.ep = Episode.objects.create(season=season, number=1, title="E1",
                                         status="published", video=self.video)

    def test_play_lists_ready_captions(self):
        Caption.objects.create(video=self.video, language="en", label="English")
        Caption.objects.create(video=self.video, language="es", label="Español", ready=False)
        self.client.force_authenticate(self.user)
        r = self.client.get(f"/api/play/{self.ep.id}")
        self.assertEqual(r.status_code, 200)
        langs = [c["language"] for c in r.data["captions"]]
        self.assertEqual(langs, ["en"])                 # only the ready one
        self.assertEqual(r.data["captions"][0]["label"], "English")
