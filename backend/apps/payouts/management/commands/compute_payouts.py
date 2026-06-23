"""
Compute creator earnings for a revenue period (watch-time pro-rata).

    python manage.py compute_payouts --start 2026-06-01 --end 2026-07-01 --pool-cents 500000

Creates a PayoutPeriod and its CreatorEarning rows. Re-running the same window updates in place.
Then review in /admin and pay with `run_payouts`.
"""
from datetime import datetime, timezone as tz

from django.core.management.base import BaseCommand, CommandError

from apps.payouts.models import PayoutPeriod
from apps.payouts.services import compute_earnings


def _parse(d):
    return datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=tz.utc)


class Command(BaseCommand):
    help = "Compute creator earnings for a period from watch-time pro-rata."

    def add_arguments(self, parser):
        parser.add_argument("--start", required=True, help="inclusive, YYYY-MM-DD (UTC)")
        parser.add_argument("--end", required=True, help="exclusive, YYYY-MM-DD (UTC)")
        parser.add_argument("--pool-cents", type=int, required=True,
                            help="subscription revenue to distribute, in cents")
        parser.add_argument("--fee-bps", type=int, default=3000,
                            help="platform cut in basis points (default 3000 = 30%%)")

    def handle(self, *args, **o):
        try:
            start, end = _parse(o["start"]), _parse(o["end"])
        except ValueError as e:
            raise CommandError(f"bad date: {e}")
        if end <= start:
            raise CommandError("--end must be after --start")

        period, _ = PayoutPeriod.objects.update_or_create(
            period_start=start, period_end=end,
            defaults={"revenue_pool_cents": o["pool_cents"], "platform_fee_bps": o["fee_bps"]},
        )
        res = compute_earnings(period)
        self.stdout.write(self.style.SUCCESS(
            f"Period {period.id}: {res['creators']} creator(s), "
            f"{res['total_seconds']}s watched, {res['distributed_cents']/100:.2f} distributed. "
            f"Review in /admin, then: python manage.py run_payouts {period.id}"))
