"""
Load a library in one shot from a manifest.

    python manage.py bulk_ingest --json library.json
    python manage.py bulk_ingest --csv  library.csv  --publish
    python manage.py bulk_ingest --json library.json --no-pull   # create metadata, skip video pull

JSON is nested (shows→seasons→episodes); CSV is flat (one row per episode). Episodes with a
`source_url` are pulled into Cloudflare and transcoded; with a `cf_uid` they reuse an existing
asset. Idempotent — re-run to update. See docs/BULK_INGEST.md for the schema.
"""
import csv
import json

from django.core.management.base import BaseCommand, CommandError

from apps.cms.ingest import csv_rows_to_manifest, ingest_manifest


class Command(BaseCommand):
    help = "Bulk-create shows/episodes (and pull videos) from a JSON or CSV manifest."

    def add_arguments(self, parser):
        parser.add_argument("--json", help="path to a nested JSON manifest")
        parser.add_argument("--csv", help="path to a flat CSV (one row per episode)")
        parser.add_argument("--publish", action="store_true",
                            help="default new items to published instead of draft")
        parser.add_argument("--no-pull", action="store_true",
                            help="don't pull source_url videos into Cloudflare")

    def handle(self, *args, **o):
        if not o.get("json") and not o.get("csv"):
            raise CommandError("pass --json <file> or --csv <file>")
        try:
            if o.get("json"):
                with open(o["json"]) as f:
                    data = json.load(f)
            else:
                with open(o["csv"], newline="") as f:
                    data = csv_rows_to_manifest(list(csv.DictReader(f)))
        except (OSError, ValueError) as e:
            raise CommandError(f"could not read manifest: {e}")

        s = ingest_manifest(data, pull_video=not o["no_pull"],
                            default_status="published" if o["publish"] else "draft")
        self.stdout.write(self.style.SUCCESS(
            f"shows +{s['shows_created']} (~{s['shows_updated']} updated) · "
            f"episodes +{s['episodes_created']} (~{s['episodes_updated']}) · "
            f"videos queued {s['videos_queued']} (skipped {s['videos_skipped']})"))
        for err in s["errors"]:
            self.stdout.write(self.style.WARNING(f"  ! {err['show']}: {err['error']}"))
