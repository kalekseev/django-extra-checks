from typing import Any, Iterable, Iterator, List, Optional

import django.core.checks

from .. import CheckId
from ..registry import ChecksConfig, registry
from .base_checks import BaseCheck


@registry.add_handler("extra_checks_selfcheck")
def check_extra_checks_health(
    checks: Iterable["CheckConfig"],
    config: ChecksConfig,
    app_configs: Optional[List[Any]] = None,
    **kwargs: Any,
) -> Iterator[django.core.checks.CheckMessage]:
    for check in checks:
        yield from check(config, None)


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


@registry.register("extra_checks_selfcheck")
class CheckConfig(BaseCheck):
    Id = CheckId.X001
    level = django.core.checks.CRITICAL

    def apply(
        self, obj: ChecksConfig, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if obj.errors:
            yield self.message(
                "Invalid EXTRA_CHECKS config.",
                hint="Fix EXTRA_CHECKS in your settings. Errors:\n"
                + (dict_to_text(obj.errors) if obj.errors else "No details."),
            )
