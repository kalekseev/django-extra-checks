import textwrap

import django.core.checks
import pytest

from extra_checks.check_id import CheckId
from extra_checks.checks import (
    CheckConfig,
    CheckFieldFileUploadTo,
    CheckFieldForeignKeyIndex,
    check_extra_checks_health,
)
from extra_checks.checks.base_checks import BaseCheck
from extra_checks.registry import Registry
from extra_checks.utils import collect_subclasses


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


def test_unique_check_ids():
    pytest.importorskip("rest_framework")
    used_checks = [
        c.Id for c in collect_subclasses(BaseCheck.__subclasses__()) if hasattr(c, "Id")
    ]
    unused = CheckId._value2member_map_.keys() - set(used_checks)
    assert not unused, "Not all CheckIds used."
    dups = {c.value for c in used_checks if used_checks.count(c) > 1}
    assert not dups, "CheckIds must be unique per Check."
