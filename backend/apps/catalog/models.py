import uuid

from django.conf import settings
from django.db import models

DRAFT, PUBLISHED = "draft", "published"
STATUS_CHOICES = [(DRAFT, "draft"), (PUBLISHED, "published")]


class Video(models.Model):
    """A video asset, 1:1 with a Cloudflare Stream upload. The backend never stores the file —
    only the Stream UID + readiness flag set by Cloudflare's transcode webhook."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cf_stream_uid = models.CharField(max_length=128, blank=True)
    drm_enabled = models.BooleanField(default=True)
    duration_s = models.IntegerField(default=0)
    ready = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cf_stream_uid or str(self.id)


class Show(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # The creator who owns this show and earns from it. Null = platform-owned original
    # (revenue stays with the platform, no payout). Set this to make a show pay a creator.
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              related_name="owned_shows", on_delete=models.SET_NULL)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    poster_url = models.URLField(blank=True)
    hero_url = models.URLField(blank=True)
    genre = models.JSONField(default=list, blank=True)        # list[str] (portable across DBs)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Season(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    show = models.ForeignKey(Show, related_name="seasons", on_delete=models.CASCADE)
    number = models.IntegerField(default=1)
    title = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["number"]


class Episode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    season = models.ForeignKey(Season, related_name="episodes", on_delete=models.CASCADE)
    number = models.IntegerField(default=1)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(blank=True)
    duration_s = models.IntegerField(default=0)
    video = models.ForeignKey(Video, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.title} (S{self.season.number}E{self.number})"


class WatchProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    position_s = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "episode")
