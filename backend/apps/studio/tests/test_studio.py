"""Self-serve creator studio: role gating, owner-scoping (no cross-creator access), submit flow."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.catalog.models import Episode, Season, Show, Video

User = get_user_model()


class StudioTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice@test.test", "pw12345678")
        self.bob = User.objects.create_user("bob@test.test", "pw12345678")

    def test_non_creator_is_blocked_until_enabled(self):
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.get("/api/studio/shows").status_code, 403)
        self.assertEqual(self.client.post("/api/studio/enable").status_code, 200)
        self.assertEqual(self.client.get("/api/studio/shows").status_code, 200)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.is_creator)

    def test_created_show_is_owned_by_uploader_and_drafts(self):
        self.client.force_authenticate(self.alice)
        self.client.post("/api/studio/enable")
        r = self.client.post("/api/studio/shows", {"title": "Alice Doc"}, format="json")
        self.assertEqual(r.status_code, 200)
        show = Show.objects.get(id=r.data["id"])
        self.assertEqual(show.owner_id, self.alice.id)
        self.assertEqual(show.status, "draft")        # creators cannot self-publish
        self.assertTrue(show.slug)                     # auto-slugged, unique

    def test_cannot_touch_another_creators_show(self):
        others = Show.objects.create(title="Bob Show", slug="bob-show", owner=self.bob)
        self.client.force_authenticate(self.alice)
        self.client.post("/api/studio/enable")
        # Update attempt on Bob's show → 404 (scoped lookup, no leak).
        r = self.client.post("/api/studio/shows",
                             {"id": str(others.id), "title": "hijack"}, format="json")
        self.assertEqual(r.status_code, 404)
        # And it can't be added to Alice's listing.
        listing = self.client.get("/api/studio/shows")
        self.assertEqual(listing.data["shows"], [])

    def test_submit_requires_an_episode_with_video(self):
        self.client.force_authenticate(self.alice)
        self.client.post("/api/studio/enable")
        show = Show.objects.create(title="Doc", slug="doc", owner=self.alice)
        # No episodes yet → rejected.
        r = self.client.post("/api/studio/submit", {"show": str(show.id)}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"], "no_episodes")
        # Add a season + episode with a video, then submit succeeds → pending.
        season = Season.objects.create(show=show, number=1)
        video = Video.objects.create(cf_stream_uid="uid", ready=True)
        Episode.objects.create(season=season, number=1, title="E1", video=video)
        r = self.client.post("/api/studio/submit", {"show": str(show.id)}, format="json")
        self.assertEqual(r.status_code, 200)
        show.refresh_from_db()
        self.assertEqual(show.status, "pending")

    def test_pending_show_is_not_public(self):
        Show.objects.create(title="Secret", slug="secret", owner=self.alice, status="pending")
        r = self.client.get("/api/catalog")          # public browse
        self.assertEqual(r.data["shows"], [])

    def test_episode_status_is_owner_scoped(self):
        show = Show.objects.create(title="Doc", slug="doc", owner=self.alice)
        season = Season.objects.create(show=show, number=1)
        video = Video.objects.create(cf_stream_uid="uid", ready=True)
        ep = Episode.objects.create(season=season, number=1, title="E1", video=video)

        self.client.force_authenticate(self.alice)
        self.client.post("/api/studio/enable")
        r = self.client.get(f"/api/studio/episodes/{ep.id}/status")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["ready"])

        # Bob cannot see Alice's episode status.
        self.client.force_authenticate(self.bob)
        self.client.post("/api/studio/enable")
        self.assertEqual(
            self.client.get(f"/api/studio/episodes/{ep.id}/status").status_code, 404)
