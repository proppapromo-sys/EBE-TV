"""Cloudflare ingest hardening: webhook signature auth + status-poll reconciliation (mocked HTTP)."""
import hashlib
import hmac
import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.catalog.models import Video
from apps.cms import cloudflare


def _sig(secret, t, body: bytes):
    mac = hmac.new(secret.encode(), f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    return f"time={t},sig1={mac}"


class WebhookSignatureTests(TestCase):
    @override_settings(CF_WEBHOOK_SECRET="whsec")
    def test_verify_accepts_valid_and_rejects_tampered(self):
        body = b'{"uid":"x","readyToStream":true}'
        good = _sig("whsec", "1700000000", body)
        self.assertTrue(cloudflare.verify_webhook_signature(body, good))
        # Wrong body, missing/garbage headers → rejected.
        self.assertFalse(cloudflare.verify_webhook_signature(b'{"uid":"y"}', good))
        self.assertFalse(cloudflare.verify_webhook_signature(body, "time=1,sig1=deadbeef"))
        self.assertFalse(cloudflare.verify_webhook_signature(body, ""))

    @override_settings(CF_WEBHOOK_SECRET="")
    def test_verification_disabled_without_secret(self):
        self.assertTrue(cloudflare.verify_webhook_signature(b"{}", ""))

    @override_settings(CF_WEBHOOK_SECRET="whsec")
    def test_webhook_endpoint_enforces_signature(self):
        video = Video.objects.create(cf_stream_uid="uid-1", ready=False)
        body = json.dumps({"uid": "uid-1", "readyToStream": True, "duration": 90}).encode()
        client = APIClient()

        # No/!invalid signature → 403, video stays not ready.
        r = client.post("/api/webhooks/cloudflare", data=body, content_type="application/json")
        self.assertEqual(r.status_code, 403)
        video.refresh_from_db()
        self.assertFalse(video.ready)

        # Valid signature → flips ready + duration.
        r = client.post("/api/webhooks/cloudflare", data=body, content_type="application/json",
                        HTTP_WEBHOOK_SIGNATURE=_sig("whsec", "1700000000", body))
        self.assertEqual(r.status_code, 200)
        video.refresh_from_db()
        self.assertTrue(video.ready)
        self.assertEqual(video.duration_s, 90)


class StatusPollTests(TestCase):
    @override_settings(CF_ACCOUNT_ID="acct", CF_API_TOKEN="tok")
    def test_get_video_status_maps_fields(self):
        fake = type("R", (), {"json": lambda self: {
            "success": True,
            "result": {"readyToStream": True, "duration": 123, "status": {"state": "ready"}}}})()
        with patch("apps.cms.cloudflare.requests.get", return_value=fake):
            st = cloudflare.get_video_status("uid-9")
        self.assertEqual(st, {"ok": True, "ready": True, "state": "ready", "duration_s": 123})

    @override_settings(CF_ACCOUNT_ID="acct", CF_API_TOKEN="tok")
    def test_sync_command_flips_ready(self):
        from django.core.management import call_command
        from io import StringIO

        v = Video.objects.create(cf_stream_uid="uid-2", ready=False)
        fake = type("R", (), {"json": lambda self: {
            "success": True, "result": {"readyToStream": True, "duration": 60}}})()
        out = StringIO()
        with patch("apps.cms.cloudflare.requests.get", return_value=fake):
            call_command("sync_video_status", stdout=out)
        v.refresh_from_db()
        self.assertTrue(v.ready)
        self.assertEqual(v.duration_s, 60)
