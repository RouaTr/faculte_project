from django.apps import AppConfig


class FilieresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "filieres"
    verbose_name = "Filières"

    def ready(self):
        from . import signals  # noqa: F401
