import ast
from abc import abstractmethod
from typing import Any, Iterator, Type

import django.core.checks
from django import forms
from django.db import models

from .. import CheckId
from ..ast import FieldAST
from ..controller import register
from ..forms import BaseCheckForm
from .base_checks import BaseCheck, BaseCheckMixin


class CheckModelField(BaseCheck):
    @abstractmethod
    def apply(
        self,
        field: models.fields.Field,
        *,
        field_ast: FieldAST,
        model: Type[models.Model],
    ) -> Iterator[django.core.checks.CheckMessage]:
        raise NotImplementedError()


class GettTextFuncForm(BaseCheckForm):
    gettext_func = forms.CharField(required=False)


class GetTextMixin(BaseCheckMixin):
    settings_form_class = GettTextFuncForm

    def __init__(self, gettext_func: str, **kwargs: Any) -> None:
        self.gettext_func = gettext_func or "_"
        super().__init__(**kwargs)

    def _is_gettext_node(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == self.gettext_func
        )


@register(django.core.checks.Tags.models)
class CheckFieldVerboseName(CheckModelField):
    Id = CheckId.X050

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not field_ast.verbose_name:
            yield self.message(
                "Field has no verbose name.",
                hint="Set verbose name on the field.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckFieldVerboseNameGettext(GetTextMixin, CheckModelField):
    Id = CheckId.X051

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field_ast.verbose_name and not self._is_gettext_node(field_ast.verbose_name):
            yield self.message(
                "Verbose name should use gettext.",
                hint="Use gettext on the verbose name.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckFieldVerboseNameGettextCase(GetTextMixin, CheckModelField):
    Id = CheckId.X052

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, **kwargs: Any
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
class CheckFieldHelpTextGettext(GetTextMixin, CheckModelField):
    Id = CheckId.X053

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field_ast.help_text and not self._is_gettext_node(field_ast.help_text):
            yield self.message(
                "Help text should use gettext.",
                hint="Use gettext on the help text.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckFieldFileUploadTo(CheckModelField):
    Id = CheckId.X054

    def apply(
        self, field: models.fields.Field, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, models.FileField):
            if not field.upload_to:
                yield self.message(
                    f'Field "{field.name}" must have non empty "upload_to" attribute.',
                    hint='Set "upload_to" on the field.',
                    obj=field,
                )


@register(django.core.checks.Tags.models)
class CheckFieldTextNull(CheckModelField):
    Id = CheckId.X055

    def apply(
        self, field: models.fields.Field, **kwargs: Any
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
class CheckFieldNullBoolean(CheckModelField):
    Id = CheckId.X056

    def apply(
        self, field: models.fields.Field, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, models.NullBooleanField):
            yield self.message(
                f'Field "{field.name}" should be `BooleanField` with attribute `null=True`.',
                hint="Replace `NullBooleanField` by `BooleanField` with attribute `null=True`.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckFieldNullFalse(CheckModelField):
    Id = CheckId.X057

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field.null is False and "null" in field_ast.kwargs:
            yield self.message(
                "Argument `null=False` is default.",
                hint="Remove `null=False` from field arguments.",
                obj=field,
            )


class CheckFieldForeignKeyIndexForm(BaseCheckForm):
    when = forms.ChoiceField(
        choices=[("unique_together", "unique_together"), ("always", "always")],
        required=False,
    )


@register(django.core.checks.Tags.models)
class CheckFieldForeignKeyIndex(CheckModelField):
    Id = CheckId.X058
    settings_form_class = CheckFieldForeignKeyIndexForm

    def __init__(self, when: str, **kwargs: Any) -> None:
        self.when = when or "unique_together"
        super().__init__(**kwargs)

    def apply(
        self,
        field: models.fields.Field,
        field_ast: FieldAST,
        model: Type[models.Model],
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field.many_to_one and field_ast.kwargs.get("db_index") is None:  # type: ignore
            if self.when == "unique_together":
                if any(field.name in index for index in model._meta.unique_together):
                    yield self.message(
                        "ForeignKey must set `db_index` explicitly if it present in unique_together.",
                        hint="Specify `db_index` field argument.",
                        obj=field,
                    )
            else:
                yield self.message(
                    "ForeignKey must set `db_index` explicitly.",
                    hint="Specify `db_index` field argument.",
                    obj=field,
                )
