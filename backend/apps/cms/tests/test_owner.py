"""CMS show creation assigns ownership so creators earn from their own uploads."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.catalog.models import Show

User = get_user_model()


class CmsOwnerTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff@ebe.tv", "pw12345678", is_staff=True)
        self.other = User.objects.create_user("other@ebe.tv", "pw12345678", is_staff=True)

    def test_create_defaults_owner_to_uploader(self):
        self.client.force_authenticate(self.staff)
        r = self.client.post("/api/cms/shows",
                             {"title": "Mine", "slug": "mine"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["owner"], self.staff.id)
        self.assertEqual(r.data["owner_email"], "staff@ebe.tv")

    def test_explicit_owner_is_respected(self):
        # Admin assigning a show on a creator's behalf.
        self.client.force_authenticate(self.staff)
        r = self.client.post("/api/cms/shows",
                             {"title": "Theirs", "slug": "theirs", "owner": str(self.other.id)},
                             format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["owner"], self.other.id)

    def test_update_does_not_clobber_owner(self):
        show = Show.objects.create(title="Keep", slug="keep", owner=self.other)
        self.client.force_authenticate(self.staff)
        r = self.client.post("/api/cms/shows",
                             {"id": str(show.id), "description": "edited"}, format="json")
        self.assertEqual(r.status_code, 200)
        show.refresh_from_db()
        self.assertEqual(show.owner_id, self.other.id)   # editor didn't steal ownership
