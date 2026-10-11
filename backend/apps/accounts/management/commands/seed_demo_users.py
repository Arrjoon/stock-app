from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create one demo user per role. Passwords come from environment variables."

    def handle(self, *args, **options):
        specs = [
            {
                "email": "admin@example.com",
                "username": "admin",
                "role": User.Role.ADMIN,
                "password": settings.SEED_ADMIN_PASSWORD,
                "env_name": "SEED_ADMIN_PASSWORD",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "analyst@example.com",
                "username": "analyst",
                "role": User.Role.ANALYST,
                "password": settings.SEED_ANALYST_PASSWORD,
                "env_name": "SEED_ANALYST_PASSWORD",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "viewer@example.com",
                "username": "viewer",
                "role": User.Role.VIEWER,
                "password": settings.SEED_VIEWER_PASSWORD,
                "env_name": "SEED_VIEWER_PASSWORD",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        missing = [spec["env_name"] for spec in specs if not spec["password"]]
        if missing:
            raise CommandError(
                "Set these environment variables before seeding demo users: "
                + ", ".join(missing)
            )

        for spec in specs:
            user, created = User.objects.update_or_create(
                email=spec["email"],
                defaults={
                    "username": spec["username"],
                    "role": spec["role"],
                    "is_staff": spec["is_staff"],
                    "is_superuser": spec["is_superuser"],
                    "is_active": True,
                },
            )
            user.set_password(spec["password"])
            user.save()
            action = "created" if created else "updated"
            self.stdout.write(f"{action} {spec['role']} user {spec['email']}")
