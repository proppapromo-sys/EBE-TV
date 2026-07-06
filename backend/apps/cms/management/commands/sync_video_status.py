"""
Reconcile not-yet-ready videos with Cloudflare — the webhook-free path to flipping `ready`.

    python manage.py sync_video_status            # poll all not-ready videos
    python manage.py sync_video_status --uid <x>  # just one

Run on a short interval (cron) so uploads still go live even before the transcode webhook is
configured, or to backfill if a webhook delivery is missed.
"""
from django.core.management.base import BaseCommand

from apps.catalog.models import Video
from apps.cms import cloudflare


class Command(BaseCommand):
    help = "Poll Cloudflare for transcode status and flip Video.ready."

    def add_arguments(self, parser):
        parser.add_argument("--uid", help="only this Cloudflare Stream UID")

    def handle(self, *args, **o):
        if not cloudflare.configured():
            self.stdout.write(self.style.WARNING("Cloudflare not configured; nothing to do."))
            return
        qs = Video.objects.filter(ready=False).exclude(cf_stream_uid="")
        if o.get("uid"):
            qs = qs.filter(cf_stream_uid=o["uid"])
        flipped = 0
        for v in qs:
            st = cloudflare.get_video_status(v.cf_stream_uid)
            if st.get("ok") and st.get("ready"):
                Video.objects.filter(pk=v.pk).update(
                    ready=True, duration_s=st.get("duration_s") or v.duration_s)
                flipped += 1
        self.stdout.write(self.style.SUCCESS(f"checked {qs.count()}, now ready: {flipped}"))
