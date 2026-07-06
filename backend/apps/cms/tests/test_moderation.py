"""Moderation queue: list pending, approve (publish show + ready episodes), reject (→ draft)."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.catalog.models import Episode, Season, Show, Video

User = get_user_model()


class ModerationTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff@ebe.tv", "pw12345678", is_staff=True)
        self.creator = User.objects.create_user("creator@ebe.tv", "pw12345678")
        self.show = Show.objects.create(title="Pending Doc", slug="pending-doc",
                                        owner=self.creator, status="pending")
        season = Season.objects.create(show=self.show, number=1)
        video = Video.objects.create(cf_stream_uid="uid", ready=True)
        self.ep = Episode.objects.create(season=season, number=1, title="E1",
                                         status="draft", video=video)

    def test_queue_requires_staff(self):
        self.client.force_authenticate(self.creator)
        self.assertEqual(self.client.get("/api/cms/moderation").status_code, 403)

    def test_queue_lists_pending(self):
        self.client.force_authenticate(self.staff)
        r = self.client.get("/api/cms/moderation")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data["pending"]), 1)
        item = r.data["pending"][0]
        self.assertEqual(item["owner_email"], "creator@ebe.tv")
        self.assertEqual(item["ready_episodes"], 1)

    def test_approve_publishes_show_and_ready_episodes(self):
        self.client.force_authenticate(self.staff)
        r = self.client.post("/api/cms/moderation",
                             {"id": str(self.show.id), "action": "approve"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.show.refresh_from_db(); self.ep.refresh_from_db()
        self.assertEqual(self.show.status, "published")
        self.assertEqual(self.ep.status, "published")
        self.assertIsNotNone(self.ep.published_at)

    def test_reject_returns_to_draft(self):
        self.client.force_authenticate(self.staff)
        r = self.client.post("/api/cms/moderation",
                             {"id": str(self.show.id), "action": "reject"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.show.refresh_from_db()
        self.assertEqual(self.show.status, "draft")
