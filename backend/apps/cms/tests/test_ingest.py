"""Bulk ingest: nested manifest, idempotency, collections, video via cf_uid/source_url, CSV, API."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from apps.catalog.models import Collection, Episode, Season, Show
from apps.cms.ingest import csv_rows_to_manifest, ingest_manifest

User = get_user_model()


def _manifest():
    return {
        "collections": [{"slug": "originals", "title": "Originals", "position": 1}],
        "shows": [{
            "slug": "the-vault", "title": "The Vault", "genre": ["Drama"],
            "status": "published", "collections": ["originals"],
            "seasons": [{"number": 1, "episodes": [
                {"number": 1, "title": "Pilot", "cf_uid": "uid-1", "ready": True, "duration_s": 1800},
                {"number": 2, "title": "Two", "cf_uid": "uid-2"},
            ]}],
        }],
    }


class IngestManifestTests(TestCase):
    def test_creates_full_tree_and_collection(self):
        s = ingest_manifest(_manifest())
        self.assertEqual(s["shows_created"], 1)
        self.assertEqual(s["episodes_created"], 2)
        self.assertEqual(s["videos_queued"], 2)
        show = Show.objects.get(slug="the-vault")
        self.assertEqual(show.status, "published")
        self.assertEqual(Episode.objects.filter(season__show=show).count(), 2)
        # cf_uid attached, and the row membership created.
        ep1 = Episode.objects.get(season__show=show, number=1)
        self.assertEqual(ep1.video.cf_stream_uid, "uid-1")
        self.assertTrue(ep1.video.ready)
        self.assertEqual(Collection.objects.get(slug="originals").items.count(), 1)

    def test_idempotent_rerun_updates_not_duplicates(self):
        ingest_manifest(_manifest())
        s2 = ingest_manifest(_manifest())
        self.assertEqual(s2["shows_updated"], 1)
        self.assertEqual(s2["shows_created"], 0)
        self.assertEqual(Show.objects.filter(slug="the-vault").count(), 1)
        self.assertEqual(Season.objects.count(), 1)
        self.assertEqual(Episode.objects.count(), 2)
        # Video not re-attached on re-run.
        self.assertEqual(s2["videos_queued"], 0)

    def test_captions_declared_on_episode(self):
        from apps.catalog.models import Caption
        data = {"shows": [{"slug": "x", "title": "X", "seasons": [{"number": 1, "episodes": [
            {"number": 1, "title": "E1", "cf_uid": "u1",
             "captions": [{"language": "en", "label": "English"},
                          {"language": "es", "label": "Español"}]}]}]}]}
        s = ingest_manifest(data)
        self.assertEqual(s["captions_added"], 2)
        self.assertEqual(Caption.objects.filter(video__cf_stream_uid="u1").count(), 2)

    def test_owner_email_resolves(self):
        creator = User.objects.create_user("creator@ebe.tv", "pw12345678")
        data = {"shows": [{"slug": "mine", "title": "Mine", "owner_email": "creator@ebe.tv"}]}
        ingest_manifest(data)
        self.assertEqual(Show.objects.get(slug="mine").owner_id, creator.id)

    @override_settings(CF_ACCOUNT_ID="acct", CF_API_TOKEN="tok")
    def test_source_url_pulls_into_cloudflare(self):
        data = {"shows": [{"slug": "doc", "title": "Doc", "seasons": [{"number": 1, "episodes": [
            {"number": 1, "title": "E1", "source_url": "https://cdn.example.com/e1.mp4"}]}]}]}
        with patch("apps.cms.cloudflare.copy_from_url",
                   return_value={"ok": True, "uid": "pulled-uid"}) as m:
            s = ingest_manifest(data)
        m.assert_called_once()
        self.assertEqual(s["videos_queued"], 1)
        self.assertEqual(Episode.objects.get(number=1).video.cf_stream_uid, "pulled-uid")

    def test_source_url_skipped_when_cloudflare_absent(self):
        data = {"shows": [{"slug": "doc", "title": "Doc", "seasons": [{"number": 1, "episodes": [
            {"number": 1, "title": "E1", "source_url": "https://cdn.example.com/e1.mp4"}]}]}]}
        s = ingest_manifest(data)            # no CF settings → copy_from_url returns not_configured
        self.assertEqual(s["videos_queued"], 0)
        self.assertEqual(s["videos_skipped"], 1)
        self.assertIsNone(Episode.objects.get(number=1).video)

    def test_bad_show_is_isolated(self):
        data = {"shows": [{"title": "", "seasons": []}, {"slug": "ok", "title": "OK"}]}
        s = ingest_manifest(data)
        self.assertEqual(len(s["errors"]), 1)
        self.assertTrue(Show.objects.filter(slug="ok").exists())   # the good one still landed

    def test_csv_rows_group_into_shows(self):
        rows = [
            {"show_slug": "a", "show_title": "Alpha", "season_number": "1",
             "episode_number": "1", "episode_title": "A1", "source_url": "u1"},
            {"show_slug": "a", "show_title": "Alpha", "season_number": "1",
             "episode_number": "2", "episode_title": "A2"},
            {"show_slug": "b", "show_title": "Bravo", "season_number": "1",
             "episode_number": "1", "episode_title": "B1", "cf_uid": "x"},
        ]
        man = csv_rows_to_manifest(rows)
        self.assertEqual(len(man["shows"]), 2)
        a = next(s for s in man["shows"] if s["slug"] == "a")
        self.assertEqual(len(a["seasons"][0]["episodes"]), 2)


class BulkIngestApiTests(APITestCase):
    def test_requires_staff(self):
        user = User.objects.create_user("viewer@ebe.tv", "pw12345678")
        self.client.force_authenticate(user)
        r = self.client.post("/api/cms/bulk-ingest", _manifest(), format="json")
        self.assertEqual(r.status_code, 403)

    def test_staff_ingests_and_gets_summary(self):
        staff = User.objects.create_user("staff@ebe.tv", "pw12345678", is_staff=True)
        self.client.force_authenticate(staff)
        r = self.client.post("/api/cms/bulk-ingest", _manifest(), format="json")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["ok"])
        self.assertEqual(r.data["shows_created"], 1)
        self.assertEqual(r.data["episodes_created"], 2)

    def test_empty_body_rejected(self):
        staff = User.objects.create_user("staff2@ebe.tv", "pw12345678", is_staff=True)
        self.client.force_authenticate(staff)
        r = self.client.post("/api/cms/bulk-ingest", {}, format="json")
        self.assertEqual(r.status_code, 400)
