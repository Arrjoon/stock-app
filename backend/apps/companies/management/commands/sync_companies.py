from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.companies.models import Company


class Command(BaseCommand):
    help = "Upsert companies from companies.yaml by symbol."

    def handle(self, *args, **options):
        candidates = [
            Path(settings.COMPANIES_YAML) if settings.COMPANIES_YAML else None,
            settings.BASE_DIR / "companies.yaml",
            settings.BASE_DIR.parent / "companies.yaml",
        ]
        path = next((p for p in candidates if p and p.exists()), None)
        if path is None:
            raise CommandError("companies.yaml not found.")

        data = yaml.safe_load(path.read_text()) or {}
        companies = data.get("companies", [])
        if not companies:
            raise CommandError(f"No companies listed in {path}.")

        created_count = 0
        updated_count = 0
        for row in companies:
            symbol = (row.get("symbol") or "").strip().upper()
            if not symbol:
                raise CommandError("Each company must have a symbol.")
            _, created = Company.objects.update_or_create(
                symbol=symbol,
                defaults={
                    "name": row.get("name") or symbol,
                    "sector": row.get("sector") or "",
                    "aliases": row.get("aliases") or [],
                    "active": row.get("active", True),
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"Synced {len(companies)} companies from {path} "
            f"({created_count} created, {updated_count} updated)."
        )
