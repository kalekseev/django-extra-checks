from typing import Any, Iterator

import django.core.checks

from .. import CheckId
from ..controller import ChecksController, register
from .base_checks import BaseCheck


def dict_to_text(data: dict, indent_level: int = 0) -> str:
    output = []
    for field, errors in data.items():
        if not errors:
            continue
        output.append(f"{' '*indent_level * 2}* {field}")
        if isinstance(errors, dict):
            output.append(dict_to_text(errors, indent_level + 1))
        else:
            output.append(
                "\n".join(f"{' '*(indent_level * 2 + 2)}* {e}" for e in errors)
            )
    return "\n".join(output)


@register("extra_checks_selfcheck")
class CheckConfig(BaseCheck):
    Id = CheckId.X001
    level = django.core.checks.CRITICAL

    def apply(
        self, obj: ChecksController, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not obj.is_healthy:
            yield self.message(
                "Invalid EXTRA_CHECKS config.",
                hint="Fix EXTRA_CHECKS in your settings. Errors:\n"
                + (dict_to_text(obj.errors) if obj.errors else "No details."),
            )
