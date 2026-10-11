from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create admin, analyst, and viewer sign-in accounts."

    def handle(self, *args, **options):
        specs = [
            {
                "email": "admin@gmail.com",
                "username": "admin",
                "role": User.Role.ADMIN,
                "password": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "analyst@gmail.com",
                "username": "analyst",
                "role": User.Role.ANALYST,
                "password": "analyst",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "viewer@gmail.com",
                "username": "viewer",
                "role": User.Role.VIEWER,
                "password": "viewer",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for spec in specs:
            user = User.objects.filter(email=spec["email"]).first()
            if user is None:
                user = User.objects.filter(username=spec["username"]).first()
            created = user is None
            if created:
                user = User(email=spec["email"], username=spec["username"])
            user.email = spec["email"]
            if not User.objects.exclude(pk=user.pk).filter(username=spec["username"]).exists():
                user.username = spec["username"]
            user.role = spec["role"]
            user.is_staff = spec["is_staff"]
            user.is_superuser = spec["is_superuser"]
            user.is_active = True
            user.set_password(spec["password"])
            user.save()
            action = "created" if created else "updated"
            self.stdout.write(f"{action} {spec['role']} user {spec['email']}")
