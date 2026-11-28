from django.apps import AppConfig


class DrugsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.drugs"
    verbose_name = "Drug knowledge"

    def ready(self):
        from . import signals  # noqa: F401
