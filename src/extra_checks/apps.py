from django.apps import AppConfig

from . import checks  # noqa
from .registry import registry


class ExtraChecksConfig(AppConfig):
    name = "extra_checks"

    def ready(self) -> None:
        super().ready()
        registry.bind()
