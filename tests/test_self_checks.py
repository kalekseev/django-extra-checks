import textwrap

import django.core.checks

from extra_checks.checks.model_field_checks import (
    CheckFieldFileUploadTo,
    CheckFieldForeignKeyIndex,
)
from extra_checks.checks.self_checks import CheckConfig, check_extra_checks_health
from extra_checks.registry import Registry


def test_empty_config(registry, settings):
    settings.EXTRA_CHECKS = {}
    registry.bind()
    assert registry.is_healthy
    assert len(registry.registered_checks) == 1
    assert len(registry.enabled_checks) == 1

    settings.EXTRA_CHECKS = {"checks": []}
    registry = Registry()
    registry._register(["extra_checks_selfcheck"], CheckConfig)
    registry.bind()
    assert registry.is_healthy
    assert len(registry.registered_checks) == 1
    assert len(registry.enabled_checks) == 1


def test_error_formatting(registry, settings):
    settings.EXTRA_CHECKS = {
        "checks": [
            CheckFieldFileUploadTo.Id.value,
            {"id": CheckFieldForeignKeyIndex.Id.value, "when": "random"},
        ]
    }
    registry._register([django.core.checks.Tags.models], CheckFieldForeignKeyIndex)
    registry._register([django.core.checks.Tags.models], CheckFieldFileUploadTo)
    registry._add_handler("extra_checks_selfcheck", check_extra_checks_health)
    handlers = registry.bind()
    assert not registry.is_healthy
    messages = list(handlers["extra_checks_selfcheck"]())
    assert len(messages) == 1
    assert (
        messages[0].hint
        == textwrap.dedent(
            f"""
            Fix EXTRA_CHECKS in your settings. Errors:
            * checks
              * {CheckFieldForeignKeyIndex.Id.value}
                * when
                  * Select a valid choice. random is not one of the available choices.
            """
        ).strip()
    )
