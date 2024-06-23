import enum
from typing import Optional, cast


class CheckId(str, enum.Enum):
    X001 = "extra-checks-config"
    X010 = "model-attribute"
    X011 = "model-meta-attribute"
    X012 = "model-admin"
    X013 = "no-unique-together"
    # X014 = "no-index-together" - removed
    X050 = "field-verbose-name"
    X051 = "field-verbose-name-gettext"
    X052 = "field-verbose-name-gettext-case"
    X053 = "field-help-text-gettext"
    X054 = "field-file-upload-to"
    X055 = "field-text-null"
    # X056 = "field-boolean-null" - removed
    X057 = "field-null"
    X058 = "field-foreign-key-db-index"
    X059 = "field-default-null"
    X060 = "field-choices-constraint"
    X061 = "field-related-name"
    X301 = "drf-model-serializer-extra-kwargs"
    X302 = "drf-model-serializer-meta-attribute"

    @classmethod
    def find_check(cls, value: str) -> Optional["CheckId"]:
        try:
            return cls(value)
        except ValueError:
            pass
        try:
            return cast(CheckId, cls._member_map_[value])
        except KeyError:
            pass
        return None


ALL_CHECKS_NAMES = frozenset(CheckId._value2member_map_.keys())
