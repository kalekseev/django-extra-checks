import enum


class CheckId(str, enum.Enum):
    X001 = "extra-checks-config"
    X010 = "model-attribute"
    X011 = "model-meta-attribute"
    X012 = "model-admin"
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
    X301 = "drf-model-serializer-extra-kwargs"
    X302 = "drf-model-serializer-meta-attribute"
