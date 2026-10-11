import logging

from django.core.management.base import BaseCommand

from apps.crawling.sync import enqueue_missing

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Queue the first price, floorsheet, and news fetch when those tables are empty."

    def handle(self, *args, **options):
        try:
            queued = enqueue_missing()
        except Exception as exc:  # noqa: BLE001
            logger.warning("bootstrap sync skipped: %s", exc)
            self.stdout.write(f"bootstrap sync skipped: {exc}")
            return
        if not queued:
            self.stdout.write("Market data already present. Periodic Beat schedule is unchanged.")
            return
        for row in queued:
            self.stdout.write(f"queued {row['kind']} {row['portal']} run={row['id']}")
