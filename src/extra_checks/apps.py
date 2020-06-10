from django.apps import AppConfig


class ExtraChecksConfig(AppConfig):
    name = "extra_checks"

    def ready(self) -> None:
        super(ExtraChecksConfig, self).ready()
        from .controller import registry
        from . import checks  # noqa

        registry.finish()
