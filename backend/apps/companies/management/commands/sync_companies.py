from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Load companies.yaml (stub — does not write to the database yet)."

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
        self.stdout.write(
            f"Loaded {len(companies)} companies from {path} (sync not implemented)."
        )
        for company in companies:
            symbol = company.get("symbol", "?")
            name = company.get("name", "")
            aliases = ", ".join(company.get("aliases") or [])
            self.stdout.write(f"  {symbol}: {name} [{aliases}]")
