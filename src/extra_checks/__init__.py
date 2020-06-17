import enum
from typing import Any, Callable, Union


class CheckId(str, enum.Enum):
    X001 = "extra-checks-config"
    X010 = "model-attribute"
    X011 = "model-meta-attribute"
    X050 = "field-verbose-name"
    X051 = "field-verbose-name-gettext"
    X052 = "field-verbose-name-gettext-case"
    X053 = "field-help-text-gettext"
    X054 = "field-file-upload-to"
    X055 = "field-text-null"
    X056 = "field-boolean-null"
    X057 = "field-null"
    X058 = "field-foreign-key-db-index"


_IGNORED = {}

EXTRA_CHECKS_ALL_RULES = list(CheckId.__members__.keys())


def ignore_checks(*args: Union[CheckId, str]) -> Callable[[Any], Any]:
    def f(entity: Any) -> Any:
        _IGNORED[entity] = set(args)
        return entity

    return f


default_app_config = "extra_checks.apps.ExtraChecksConfig"

__all__ = [
    "ignore_checks",
    "CheckId",
]
