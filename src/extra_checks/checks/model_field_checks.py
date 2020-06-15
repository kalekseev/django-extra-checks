import ast
from abc import abstractmethod
from typing import Any, ClassVar, Iterator, Type

import django.core.checks
from django.db import models

from .. import CheckId, forms
from ..ast import FieldAST
from ..controller import register
from .base_checks import BaseCheck


class ModelFieldCheck(BaseCheck):
    @abstractmethod
    def apply(
        self, field: models.fields.Field, field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        raise NotImplementedError()


class GetTextMixin:
    settings_form_class: ClassVar[Type[forms.CheckForm]] = forms.CheckGettTextFuncForm

    def __init__(self, gettext_func: str, **kwargs: Any) -> None:
        self.gettext_func = gettext_func or "_"
        super().__init__(**kwargs)  # type: ignore

    def _is_gettext_node(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == self.gettext_func
        )


@register(django.core.checks.Tags.models)
class CheckFieldVerboseName(ModelFieldCheck):
    Id = CheckId.X050

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not field_ast.verbose_name:
            yield self.message(
                "Field has no verbose name.",
                hint="Set verbose name on the field.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckFieldVerboseNameGettext(GetTextMixin, ModelFieldCheck):
    Id = CheckId.X051

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field_ast.verbose_name and not self._is_gettext_node(field_ast.verbose_name):
            yield self.message(
                "Verbose name should use gettext.",
                hint="Use gettext on the verbose name.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckFieldVerboseNameGettextCase(GetTextMixin, ModelFieldCheck):
    Id = CheckId.X052

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field_ast.verbose_name and self._is_gettext_node(field_ast.verbose_name):
            value = field_ast.verbose_name.args[0].s  # type: ignore
            if not all(
                w.islower() or w.isupper() or w.isdigit() for w in value.split(" ")
            ):
                yield django.core.checks.Warning(
                    "Words in verbose name must be all upper case or all lower case.",
                    hint='Change verbose name to "{}".'.format(value.lower()),
                    obj=field,
                )


@register(django.core.checks.Tags.models)
class CheckFieldHelpTextGettext(GetTextMixin, ModelFieldCheck):
    Id = CheckId.X053

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field_ast.help_text and not self._is_gettext_node(field_ast.help_text):
            yield self.message(
                "Help text should use gettext.",
                hint="Use gettext on the help text.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckFieldFileUploadTo(ModelFieldCheck):
    Id = CheckId.X054

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, models.FileField):
            if not field.upload_to:
                yield self.message(
                    f'Field "{field.name}" must have non empty "upload_to" attribute.',
                    hint='Set "upload_to" on the field.',
                    obj=field,
                )


@register(django.core.checks.Tags.models)
class CheckFieldTextNull(ModelFieldCheck):
    Id = CheckId.X055

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, (models.CharField, models.TextField)):
            if field.null:
                yield self.message(
                    f'Field "{field.name}" shouldn\'t use `null=True` '
                    "(django uses empty string for text fields).",
                    hint="Remove `null=True` attribute from the field.",
                    obj=field,
                )


@register(django.core.checks.Tags.models)
class CheckFieldNullBoolean(ModelFieldCheck):
    Id = CheckId.X056

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, models.NullBooleanField):
            yield self.message(
                f'Field "{field.name}" should be `BooleanField` with attribute `null=True`.',
                hint="Replace `NullBooleanField` by `BooleanField` with attribute `null=True`.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckFieldNullFalse(ModelFieldCheck):
    Id = CheckId.X057

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field.null is False and "null" in field_ast.kwargs:
            yield self.message(
                "Argument `null=False` is default.",
                hint="Remove `null=False` from field arguments.",
                obj=field,
            )
