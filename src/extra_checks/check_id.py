import enum
from typing import Any, Optional


class CheckId(str, enum.Enum):
    X001 = "extra-checks-config"
    X010 = "model-attribute"
    X011 = "model-meta-attribute"
    X012 = "model-admin"
    X013 = "no-unique-together"
    X014 = "no-index-together"
    X050 = "field-verbose-name"
    X051 = "field-verbose-name-gettext"
    X052 = "field-verbose-name-gettext-case"
    X053 = "field-help-text-gettext"
    X054 = "field-file-upload-to"
    X055 = "field-text-null"
    X056 = "field-boolean-null"
    X057 = "field-null"
    X058 = "field-foreign-key-db-index"
    X059 = "field-default-null"
    X060 = "field-choices-constraint"
    X301 = "drf-model-serializer-extra-kwargs"
    X302 = "drf-model-serializer-meta-attribute"

    @classmethod
    def find_check(cls, value: Any) -> Optional["CheckId"]:
        if isinstance(value, CheckId):
            return value
        try:
            return cls(value)
        except ValueError:
            pass
        try:
            return cls._member_map_[value]  # type: ignore
        except KeyError:
            pass
        return None


MODEL_META_CHECKS_NAMES = frozenset(
    (
        "model-meta-attribute",
        "no-unique-together",
        "no-index-together",
    )
)
DRF_META_CHECKS_NAMES = frozenset(
    (
        "drf-model-serializer-extra-kwargs",
        "drf-model-serializer-meta-attribute",
    )
)
ALL_CHECKS_NAMES = frozenset(CheckId._value2member_map_.keys())
