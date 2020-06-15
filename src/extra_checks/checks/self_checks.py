from typing import Any, Iterator

import django.core.checks

from .. import CheckId
from ..controller import ChecksController, register
from .base_checks import BaseCheck


@register("extra_checks_selfcheck")
class CheckX001(BaseCheck):
    Id = CheckId.X001
    level = django.core.checks.CRITICAL

    def apply(
        self, obj: ChecksController, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not obj.is_healthy:
            yield self.message(
                "Invalid EXTRA_CHECKS config.",
                hint="Fix EXTRA_CHECKS in your settings. Errors:\n"
                + (obj.errors.as_text() if obj.errors else "No details."),
            )
