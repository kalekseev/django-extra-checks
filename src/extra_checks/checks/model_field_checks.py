from abc import abstractmethod
from typing import Any, Iterator, Optional, Type

import django.core.checks
from django import forms
from django.db import models

from .. import CheckId
from ..ast import FieldASTProtocol, MissingASTError
from ..ast.protocols import DisableCommentProtocol
from ..forms import BaseCheckForm
from ..registry import registry
from .base_checks import BaseCheck, BaseCheckMixin


class CheckModelField(BaseCheck):
    @abstractmethod
    def apply(
        self,
        field: models.fields.Field,
        *,
        ast: FieldASTProtocol,
        model: Type[models.Model],
    ) -> Iterator[django.core.checks.CheckMessage]:
        raise NotImplementedError()

    def __call__(
        self, obj: Any, ast: Optional[DisableCommentProtocol] = None, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        try:
            yield from super().__call__(obj, ast=ast, **kwargs)
        except MissingASTError:
            pass

    def is_ignored(self, obj: Any) -> bool:
        if self.skipif and self.skipif(obj):
            return True
        return obj.model in self.ignore_objects or type(obj) in self.ignore_types


class GetTextMixin(BaseCheckMixin):
    class GettTextFuncForm(BaseCheckForm):
        gettext_func = forms.CharField(required=False)

    settings_form_class = GettTextFuncForm

    def __init__(self, gettext_func: str, **kwargs: Any) -> None:
        self.gettext_func = gettext_func or "_"
        super().__init__(**kwargs)


@registry.register(django.core.checks.Tags.models)
class CheckFieldVerboseName(CheckModelField):
    Id = CheckId.X050

    def apply(
        self, field: models.fields.Field, ast: FieldASTProtocol, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not ast.get_arg("verbose_name"):
            yield self.message(
                "Field has no verbose name.",
                hint="Set verbose name on the field.",
                obj=field,
            )


@registry.register(django.core.checks.Tags.models)
class CheckFieldVerboseNameGettext(GetTextMixin, CheckModelField):
    Id = CheckId.X051

    def apply(
        self, field: models.fields.Field, ast: FieldASTProtocol, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        verbose_name = ast.get_arg("verbose_name")
        if verbose_name and not (
            verbose_name.is_callable
            and verbose_name.callable_func_name == self.gettext_func
        ):
            yield self.message(
                "Verbose name should use gettext.",
                hint="Use gettext on the verbose name.",
                obj=field,
            )


@registry.register(django.core.checks.Tags.models)
class CheckFieldVerboseNameGettextCase(GetTextMixin, CheckModelField):
    Id = CheckId.X052

    def apply(
        self, field: models.fields.Field, ast: FieldASTProtocol, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        verbose_name = ast.get_arg("verbose_name")
        if verbose_name and (
            verbose_name.is_callable
            and verbose_name.callable_func_name == self.gettext_func
        ):
            value = verbose_name.get_call_first_args()
            if (
                value
                and isinstance(value, str)
                and not all(
                    w.islower() or w.isupper() or w.isdigit() for w in value.split(" ")
                )
            ):
                yield self.message(
                    "Words in verbose name must be all upper case or all lower case.",
                    hint=f'Change verbose name to "{value.lower()}".',
                    obj=field,
                )


@registry.register(django.core.checks.Tags.models)
class CheckFieldHelpTextGettext(GetTextMixin, CheckModelField):
    Id = CheckId.X053

    def apply(
        self, field: models.fields.Field, ast: FieldASTProtocol, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        help_text = ast.get_arg("help_text")
        if help_text and not (
            help_text.is_callable and help_text.callable_func_name == self.gettext_func
        ):
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
    deprecation_warnings = [
        "`field-boolean-null` check is deprecated and will be removed in version 0.14.0"
    ]

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
        self, field: models.fields.Field, ast: FieldASTProtocol, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field.null is False and ast.get_arg("null"):
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
            yield from entry
        for entry in model._meta.index_together:
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
        ast: FieldASTProtocol,
        model: Type[models.Model],
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, models.fields.related.RelatedField):
            if field.many_to_one and not ast.get_arg("db_index"):
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
class CheckFieldRelatedName(CheckModelField):
    Id = CheckId.X061

    def apply(
        self,
        field: models.fields.Field,
        ast: FieldASTProtocol,
        model: Type[models.Model],
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, models.fields.related.RelatedField):
            if not field.remote_field.related_name:
                yield self.message(
                    "Related fields must set `related_name` explicitly.",
                    hint="Specify `related_name` field argument. Use `related_name='+'` to not create a backwards relation.",
                    obj=field,
                )


@registry.register(django.core.checks.Tags.models)
class CheckFieldDefaultNull(CheckModelField):
    Id = CheckId.X059

    def apply(
        self, field: models.fields.Field, ast: FieldASTProtocol, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field.null and field.default is None and ast.get_arg("default"):
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
        self,
        field: models.fields.Field,
        ast: FieldASTProtocol,
        model: Type[models.Model],
    ) -> Iterator[django.core.checks.CheckMessage]:
        choices = field.flatchoices  # type: ignore
        if choices:
            field_choices = [c[0] for c in choices]
            if field.blank and "" not in field_choices and field.empty_strings_allowed:
                field_choices.append("")
            if field.null and None not in field_choices:
                field_choices.append(None)
            in_name = f"{field.name}__in"
            for constraint in model._meta.constraints:
                if isinstance(constraint, models.CheckConstraint):
                    conditions = dict(constraint.check.children)  # type: ignore
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
