from django.core.management.base import BaseCommand

from apps.analysis.compute import compute_active_companies


class Command(BaseCommand):
    help = "Compute VWAP, pressure, volume anomalies, and broker buy/sell behavior."

    def handle(self, *args, **options):
        written = compute_active_companies()
        self.stdout.write(f"computed {written} analysis rows")
