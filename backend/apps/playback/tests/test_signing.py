"""Signed playback tokens: a real RS256 sign→verify roundtrip, and base64-PEM acceptance."""
import base64
import time

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase, override_settings

from apps.playback import cloudflare


def _rsa_pem():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()).decode()
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return private_pem, public_pem


class SignedTokenTests(TestCase):
    def setUp(self):
        self.priv, self.pub = _rsa_pem()

    def test_token_roundtrip_and_claims(self):
        with override_settings(CF_STREAM_SIGNING_KEY_ID="key-123",
                               CF_STREAM_SIGNING_KEY_PEM=self.priv,
                               PLAYBACK_TOKEN_TTL=120):
            self.assertTrue(cloudflare.configured())
            token = cloudflare.signed_token("vid-uid", user_id="u-1")
            # A client (Cloudflare) verifies with the public key — must validate cleanly.
            decoded = jwt.decode(token, self.pub, algorithms=["RS256"])
            self.assertEqual(decoded["sub"], "vid-uid")
            self.assertEqual(decoded["kid"], "key-123")
            self.assertEqual(jwt.get_unverified_header(token)["kid"], "key-123")
            self.assertLessEqual(decoded["exp"] - decoded["nbf"], 120)
            self.assertGreaterEqual(decoded["exp"], int(time.time()))

    def test_accepts_base64_encoded_pem(self):
        # Cloudflare's /stream/keys returns the key base64-encoded; signing must still work.
        b64 = base64.b64encode(self.priv.encode()).decode()
        with override_settings(CF_STREAM_SIGNING_KEY_ID="key-123",
                               CF_STREAM_SIGNING_KEY_PEM=b64):
            token = cloudflare.signed_token("vid-uid", user_id="u-1")
            decoded = jwt.decode(token, self.pub, algorithms=["RS256"])
            self.assertEqual(decoded["sub"], "vid-uid")

    def test_manifests_embed_token(self):
        with override_settings(CF_CUSTOMER_SUBDOMAIN="customer-abc.cloudflarestream.com"):
            m = cloudflare.manifests("TOKEN123")
            self.assertIn("/TOKEN123/manifest/video.mpd", m["dash"])
            self.assertIn("/TOKEN123/manifest/video.m3u8", m["hls"])
