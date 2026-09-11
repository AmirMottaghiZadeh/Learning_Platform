"""Create (or update) the admin superuser from environment variables.

Exists because several free/low-tier hosts (this project has hit it on both
Runflare and Render's free plan) don't give an interactive shell or one-off
job runner, so the usual `manage.py createsuperuser` has nowhere to run. Safe
to call on every deploy: idempotent (get-or-create by username), and only
acts when the three env vars are actually set — otherwise it's a silent
no-op, so it's fine to leave permanently wired into release.sh.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the superuser named by DJANGO_SUPERUSER_* env vars."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=None)
        parser.add_argument("--email", default=None)
        parser.add_argument("--password", default=None)

    def handle(self, *args, **options):
        import os

        username = options["username"] or os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = options["email"] or os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = options["password"] or os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not (username and email and password):
            self.stdout.write("bootstrap_superuser: DJANGO_SUPERUSER_* not fully set, skipping.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f"bootstrap_superuser: {'created' if created else 'updated'} '{username}'."
        ))
