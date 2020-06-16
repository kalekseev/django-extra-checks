import django.core.checks

from extra_checks.checks import model_field_checks
from tests.example.models import Article


def test_check_field_verbose_name(registry, use_models, settings):
    use_models(Article)
    settings.EXTRA_CHECKS = {
        "checks": [model_field_checks.CheckFieldVerboseName.Id.value]
    }
    registry._register(
        [django.core.checks.Tags.models], model_field_checks.CheckFieldVerboseName
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert not messages
