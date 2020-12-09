import ast
from abc import abstractmethod
from typing import Any, Iterator, Type, Union

import django.core.checks
from django import forms
from django.db import models

from .. import CheckId
from ..ast import FieldAST
from ..forms import BaseCheckForm
from ..registry import registry
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

    def is_ignored(self, obj: Any) -> bool:
        return obj.model in self.ignore_objects or type(obj) in self.ignore_types


class GetTextMixin(BaseCheckMixin):
    class GettTextFuncForm(BaseCheckForm):
        gettext_func = forms.CharField(required=False)

    settings_form_class = GettTextFuncForm

    def __init__(self, gettext_func: str, **kwargs: Any) -> None:
        self.gettext_func = gettext_func or "_"
        super().__init__(**kwargs)

    def _is_gettext_node(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == self.gettext_func
        )


def get_verbose_name(
    field: models.fields.Field, field_ast: FieldAST
) -> Union[None, ast.Constant, ast.Call]:
    result = field_ast.verbose_name
    if result:
        return result
    if isinstance(field, models.fields.related.RelatedField):
        return None
    if field_ast.args:
        node = field_ast.args[0]
        if isinstance(node, ast.Call) and hasattr(node.func, "id"):
            return node
        elif isinstance(node, (ast.Constant, ast.Str)):
            return node
    return None


@registry.register(django.core.checks.Tags.models)
class CheckFieldVerboseName(CheckModelField):
    Id = CheckId.X050

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        verbose_name = get_verbose_name(field, field_ast)
        if not verbose_name:
            yield self.message(
                "Field has no verbose name.",
                hint="Set verbose name on the field.",
                obj=field,
            )


@registry.register(django.core.checks.Tags.models)
class CheckFieldVerboseNameGettext(GetTextMixin, CheckModelField):
    Id = CheckId.X051

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        verbose_name = get_verbose_name(field, field_ast)
        if verbose_name and not self._is_gettext_node(verbose_name):
            yield self.message(
                "Verbose name should use gettext.",
                hint="Use gettext on the verbose name.",
                obj=field,
            )


@registry.register(django.core.checks.Tags.models)
class CheckFieldVerboseNameGettextCase(GetTextMixin, CheckModelField):
    Id = CheckId.X052

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        verbose_name = get_verbose_name(field, field_ast)
        if verbose_name and self._is_gettext_node(verbose_name):
            value = verbose_name.args[0].s  # type: ignore
            if not all(
                w.islower() or w.isupper() or w.isdigit() for w in value.split(" ")
            ):
                yield self.message(
                    "Words in verbose name must be all upper case or all lower case.",
                    hint='Change verbose name to "{}".'.format(value.lower()),
                    obj=field,
                )


@registry.register(django.core.checks.Tags.models)
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


@registry.register(django.core.checks.Tags.models)
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


@registry.register(django.core.checks.Tags.models)
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


@registry.register(django.core.checks.Tags.models)
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


@registry.register(django.core.checks.Tags.models)
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


@registry.register(django.core.checks.Tags.models)
class CheckFieldForeignKeyIndex(CheckModelField):
    Id = CheckId.X058

    class CheckFieldForeignKeyIndexForm(BaseCheckForm):
        when = forms.ChoiceField(
            choices=[("indexes", "indexes"), ("always", "always")],
            required=False,
        )

    settings_form_class = CheckFieldForeignKeyIndexForm

    def __init__(self, when: str, **kwargs: Any) -> None:
        self.when = when or "indexes"
        super().__init__(**kwargs)

    @classmethod
    def get_index_values_in_meta(cls, model: Type[models.Model]) -> Iterator[str]:
        for entry in model._meta.unique_together:
            if isinstance(entry, str):
                yield entry
            else:
                yield from entry
        for entry in model._meta.index_together:
            if isinstance(entry, str):
                yield entry
            else:
                yield from entry
        for constraint in model._meta.constraints:
            if isinstance(constraint, models.UniqueConstraint):
                yield from constraint.fields
        for index in model._meta.indexes:
            yield from index.fields

    @classmethod
    def get_fields_with_indexes_in_meta(
        cls, model: Type[models.Model]
    ) -> Iterator[str]:
        for entry in cls.get_index_values_in_meta(model):
            yield entry.lstrip("-")

    def apply(
        self,
        field: models.fields.Field,
        field_ast: FieldAST,
        model: Type[models.Model],
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, models.fields.related.RelatedField):
            if field.many_to_one and field_ast.kwargs.get("db_index") is None:
                if self.when == "indexes":
                    if field.name in self.get_fields_with_indexes_in_meta(model):
                        yield self.message(
                            "ForeignKey field must set `db_index` explicitly if it present in other indexes.",
                            hint="Specify `db_index` field argument.",
                            obj=field,
                        )
                else:
                    yield self.message(
                        "ForeignKey must set `db_index` explicitly.",
                        hint="Specify `db_index` field argument.",
                        obj=field,
                    )


@registry.register(django.core.checks.Tags.models)
class CheckFieldDefaultNull(CheckModelField):
    Id = CheckId.X059

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field.null and field.default is None and "default" in field_ast.kwargs:
            yield self.message(
                "Argument `default=None` is redundant if `null=True` is set. (see docs about exceptions).",
                hint="Remove `default=None` from field arguments.",
                obj=field,
            )


@registry.register(django.core.checks.Tags.models)
class CheckFieldChoicesConstraint(CheckModelField):
    Id = CheckId.X060

    @staticmethod
    def _repr_choice(value: Any) -> str:
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    def apply(
        self, field: models.fields.Field, field_ast: FieldAST, model: Type[models.Model]
    ) -> Iterator[django.core.checks.CheckMessage]:
        choices = field.flatchoices  # type: ignore
        if choices:
            field_choices = [c[0] for c in choices]
            if field.blank and "" not in field_choices:
                field_choices.append("")
            in_name = f"{field.name}__in"
            for constraint in model._meta.constraints:
                if isinstance(constraint, models.CheckConstraint):
                    conditions = dict(constraint.check.children)
                    if in_name in conditions and set(field_choices) == set(
                        conditions[in_name]
                    ):
                        return
            check = f'models.Q({in_name}=[{", ".join([self._repr_choice(c) for c in field_choices])}])'
            yield self.message(
                "Field with choices must have companion CheckConstraint to enforce choices on database level.",
                hint=f'Add to Meta.constraints: `models.CheckConstraint(name="%(app_label)s_%(class)s_{field.name}_valid", check={check})`',
                obj=field,
            )
