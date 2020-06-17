import django.core.checks

from extra_checks.checks import model_checks
from tests.example.models import Article, Author


def test_check_model_attrs(settings, use_models, registry):
    use_models(Article)
    settings.EXTRA_CHECKS = {
        "checks": [{"id": model_checks.CheckModelAttribute.Id.value, "attrs": ["site"]}]
    }
    registry._register(
        [django.core.checks.Tags.models], model_checks.CheckModelAttribute
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert not messages
    use_models(Author)
    messages = list(controller.check_models())
    assert len(messages) == 1
    assert messages[0].id == model_checks.CheckModelAttribute.Id.name


def test_check_model_meta_attrs(settings, use_models, registry):
    use_models(Article)
    settings.EXTRA_CHECKS = {
        "checks": [
            {
                "id": model_checks.CheckModelMetaAttribute.Id.value,
                "attrs": ["verbose_name"],
            }
        ]
    }
    registry._register(
        [django.core.checks.Tags.models], model_checks.CheckModelMetaAttribute
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert not messages
    use_models(Author)
    messages = list(controller.check_models())
    assert len(messages) == 1
    assert messages[0].id == model_checks.CheckModelMetaAttribute.Id.name
