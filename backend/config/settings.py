"""
Django settings — streaming platform backend.

Designed to RUN IMMEDIATELY with zero external services (SQLite + in-memory cache) so you can
`migrate && runserver` in minute one, and to switch to the real stack (Postgres + Redis) purely
by setting DATABASE_URL / REDIS_URL — no code change. Every third-party integration (Stripe,
Cloudflare, Apple, Google) degrades gracefully when its keys are absent.
"""
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    return str(env(key, str(default))).lower() in ("1", "true", "yes", "on")


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    # local apps
    "apps.accounts",
    "apps.catalog",
    "apps.subscriptions",
    "apps.billing",
    "apps.playback",
    "apps.cms",
    "apps.payouts",
    "apps.studio",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# Database — Postgres in prod via DATABASE_URL; SQLite fallback for instant local start.
DATABASES = {
    "default": dj_database_url.parse(
        env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
    )
}

# Cache / entitlement store — Redis in prod via REDIS_URL; LocMem fallback for local.
_redis_url = env("REDIS_URL")
if _redis_url:
    CACHES = {"default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": _redis_url,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }}
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "240/min"},
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "SIGNING_KEY": env("JWT_SIGNING_KEY", SECRET_KEY),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [o for o in env("CORS_ALLOWED_ORIGINS", "").split(",") if o]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Integration config (all optional; endpoints report "not configured" when missing) ──
ENTITLEMENT_CACHE_TTL = int(env("ENTITLEMENT_CACHE_TTL", "300"))

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_MONTHLY = env("STRIPE_PRICE_MONTHLY", "")
STRIPE_PRICE_ANNUAL = env("STRIPE_PRICE_ANNUAL", "")
CHECKOUT_SUCCESS_URL = env("CHECKOUT_SUCCESS_URL", "http://localhost:3000/account?ok=1")
CHECKOUT_CANCEL_URL = env("CHECKOUT_CANCEL_URL", "http://localhost:3000/subscribe?canceled=1")

# ── Creator payouts (Stripe Connect; reuses STRIPE_SECRET_KEY) ──
# Default platform cut on creator earnings, in basis points (3000 = 30%).
PLATFORM_FEE_BPS = int(env("PLATFORM_FEE_BPS", "3000"))
STRIPE_CONNECT_RETURN_URL = env("STRIPE_CONNECT_RETURN_URL",
                                "http://localhost:3000/creator?onboarded=1")
STRIPE_CONNECT_REFRESH_URL = env("STRIPE_CONNECT_REFRESH_URL",
                                 "http://localhost:3000/creator?refresh=1")

CF_ACCOUNT_ID = env("CF_ACCOUNT_ID", "")
CF_API_TOKEN = env("CF_API_TOKEN", "")
CF_STREAM_SIGNING_KEY_ID = env("CF_STREAM_SIGNING_KEY_ID", "")
CF_STREAM_SIGNING_KEY_PEM = env("CF_STREAM_SIGNING_KEY_PEM", "")
CF_CUSTOMER_SUBDOMAIN = env("CF_CUSTOMER_SUBDOMAIN", "customer-XXXX.cloudflarestream.com")
PLAYBACK_TOKEN_TTL = int(env("PLAYBACK_TOKEN_TTL", "120"))

APPLE_ISSUER_ID = env("APPLE_ISSUER_ID", "")
APPLE_KEY_ID = env("APPLE_KEY_ID", "")
APPLE_PRIVATE_KEY = env("APPLE_PRIVATE_KEY", "")
APPLE_BUNDLE_ID = env("APPLE_BUNDLE_ID", "")

GOOGLE_SERVICE_ACCOUNT_JSON = env("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_PACKAGE_NAME = env("GOOGLE_PACKAGE_NAME", "")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
