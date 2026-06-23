"""
Pay out a computed period via Stripe Connect transfers.

    python manage.py run_payouts <period_id>           # live transfers (needs STRIPE_SECRET_KEY)
    python manage.py run_payouts <period_id> --dry-run  # mark intent only, no money moves

Idempotent per earning (Stripe idempotency key = payout-<earning_id>), so re-running after a
partial failure only retries the rows that didn't pay.
"""
from django.core.management.base import BaseCommand, CommandError

from apps.payouts.models import PayoutPeriod
from apps.payouts.services import run_payouts


class Command(BaseCommand):
    help = "Issue Stripe Connect transfers for a computed payout period."

    def add_arguments(self, parser):
        parser.add_argument("period_id")
        parser.add_argument("--dry-run", action="store_true",
                            help="record SKIPPED reasons without transferring")

    def handle(self, *args, **o):
        period = PayoutPeriod.objects.filter(id=o["period_id"]).first()
        if not period:
            raise CommandError(f"no PayoutPeriod {o['period_id']}")
        res = run_payouts(period, live=not o["dry_run"])
        self.stdout.write(self.style.SUCCESS(
            f"paid={res['paid']} skipped={res['skipped']} failed={res['failed']} "
            f"(period now {period.status})"))
