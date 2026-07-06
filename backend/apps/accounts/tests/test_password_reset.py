"""Password reset: request never leaks existence; confirm validates the signed token."""
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APITestCase

User = get_user_model()


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("u@ebe.tv", "oldpass123")

    def test_request_is_ok_even_for_unknown_email(self):
        for email in ("u@ebe.tv", "nobody@ebe.tv"):
            r = self.client.post("/api/auth/password/reset", {"email": email}, format="json")
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.data["ok"])

    def _uid_token(self, user):
        return urlsafe_base64_encode(force_bytes(user.pk)), default_token_generator.make_token(user)

    def test_confirm_sets_new_password(self):
        uid, token = self._uid_token(self.user)
        r = self.client.post("/api/auth/password/reset/confirm",
                             {"uid": uid, "token": token, "password": "brandnew123"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("brandnew123"))
        # The login endpoint accepts the new password.
        self.assertEqual(self.client.post(
            "/api/auth/login", {"email": "u@ebe.tv", "password": "brandnew123"},
            format="json").status_code, 200)

    def test_confirm_rejects_bad_token(self):
        uid, _ = self._uid_token(self.user)
        r = self.client.post("/api/auth/password/reset/confirm",
                             {"uid": uid, "token": "wrong-token", "password": "brandnew123"},
                             format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"], "invalid_or_expired")

    def test_confirm_rejects_short_password(self):
        uid, token = self._uid_token(self.user)
        r = self.client.post("/api/auth/password/reset/confirm",
                             {"uid": uid, "token": token, "password": "short"}, format="json")
        self.assertEqual(r.status_code, 400)
