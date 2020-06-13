import ast
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Iterator, List, Optional, Set, Type

import django.core.checks
from django.db import models

from . import CheckID, forms
from .ast import FieldAST, ModelAST
from .controller import ChecksController, register

MESSAGE_MAP = {
    django.core.checks.DEBUG: django.core.checks.Debug,
    django.core.checks.INFO: django.core.checks.Info,
    django.core.checks.WARNING: django.core.checks.Warning,
    django.core.checks.ERROR: django.core.checks.Error,
    django.core.checks.CRITICAL: django.core.checks.Critical,
}


class Check(ABC):
    ID: CheckID
    settings_form_class: ClassVar[Type[forms.CheckForm]] = forms.CheckForm
    level = django.core.checks.WARNING

    def __init__(self, level: int = None, ignored_objects: Set[Any] = None) -> None:
        self.level = level or self.level
        self.ignored_objects = ignored_objects or set()

    def __call__(
        self, obj: Any, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not self.is_ignored(obj):
            yield from self.apply(obj, **kwargs)  # type: ignore

    def is_ignored(self, obj: Any) -> bool:
        return obj in self.ignored_objects

    def message(
        self, message: str, hint: Optional[str] = None, obj: Any = None
    ) -> django.core.checks.CheckMessage:
        return MESSAGE_MAP[self.level](message, hint=hint, obj=obj, id=self.ID.value)


@register("extra_checks_selfcheck")
class CheckX001(Check):
    ID = CheckID.X001
    level = django.core.checks.CRITICAL

    def apply(
        self, obj: ChecksController, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not obj.is_healthy:
            yield self.message(
                "Invalid EXTRA_CHECKS config.",
                hint="Fix EXTRA_CHECKS in your settings. Errors:\n"
                + obj.errors.as_text(),  # type: ignore
            )


class ModelCheck(Check):
    @abstractmethod
    def apply(
        self, model: Type[models.Model], model_ast: ModelAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        raise NotImplementedError()


@register(django.core.checks.Tags.models)
class CheckX003(ModelCheck):
    ID = CheckID.X003
    settings_form_class = forms.CheckAttrsForm

    def __init__(self, attrs: List[str], **kwargs: Any) -> None:
        self.attrs = attrs
        super().__init__(**kwargs)

    def apply(
        self, model: Type[models.Model], model_ast: ModelAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        for attr in self.attrs:
            if (
                not model._meta.abstract
                and not model._meta.proxy
                and not hasattr(model, attr)
            ):
                yield self.message(
                    f'Each model must specify "{attr}" attribute.',
                    hint=f'Set "{attr}" attribute.',
                    obj=model,
                )


@register(django.core.checks.Tags.models)
class CheckX004(ModelCheck):
    ID = CheckID.X004
    settings_form_class = forms.CheckMetaAttrsForm

    def __init__(self, attrs: List[str], **kwargs: Any) -> None:
        self.attrs = attrs
        super().__init__(**kwargs)

    def apply(
        self, model: Type[models.Model], model_ast: ModelAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        for attr in self.attrs:
            if (
                not model._meta.abstract
                and not model._meta.proxy
                and attr not in model_ast.meta_vars
            ):
                yield self.message(
                    f'Each model must specify "{attr}" attribute in its Meta.',
                    hint=f'Set "{attr}" attribute in Meta.',
                    obj=model,
                )


class ModelFieldCheck(Check):
    @abstractmethod
    def apply(
        self, field: Type[models.fields.Field], field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        raise NotImplementedError()


@register(django.core.checks.Tags.models)
class CheckX005(ModelFieldCheck):
    ID = CheckID.X005

    def apply(
        self, field: Type[models.fields.Field], field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not field_ast.verbose_name:
            yield self.message(
                "Field has no verbose name.",
                hint="Set verbose name on the field.",
                obj=field,
            )


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
class CheckX006(GetTextMixin, ModelFieldCheck):
    ID = CheckID.X006

    def apply(
        self, field: Type[models.fields.Field], field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field_ast.verbose_name and not self._is_gettext_node(field_ast.verbose_name):
            yield self.message(
                "Verbose name should use gettext.",
                hint="Use gettext on the verbose name.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckX007(GetTextMixin, ModelFieldCheck):
    ID = CheckID.X007

    def apply(
        self, field: Type[models.fields.Field], field_ast: FieldAST
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
class CheckX008(GetTextMixin, ModelFieldCheck):
    ID = CheckID.X008

    def apply(
        self, field: Type[models.fields.Field], field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field_ast.help_text and not self._is_gettext_node(field_ast.help_text):
            yield django.core.checks.Warning(
                "Help text should use gettext.",
                hint="Use gettext on the help text.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckX002(ModelFieldCheck):
    ID = CheckID.X002

    def apply(
        self, field: Type[models.fields.Field], field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, models.FileField):
            if not field.upload_to:
                yield self.message(
                    f'Field "{field.name}" must have non empty "upload_to" attribute.',
                    hint='Set "upload_to" on the field.',
                    obj=field,
                )


@register(django.core.checks.Tags.models)
class CheckX009(ModelFieldCheck):
    ID = CheckID.X009

    def apply(
        self, field: Type[models.fields.Field], field_ast: FieldAST
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
class CheckX010(ModelFieldCheck):
    ID = CheckID.X010

    def apply(
        self, field: Type[models.fields.Field], field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if isinstance(field, models.NullBooleanField):
            yield self.message(
                f'Field "{field.name}" should be `BooleanField` with attribute `null=True`.',
                hint="Replace `NullBooleanField` by `BooleanField` with attribute `null=True`.",
                obj=field,
            )


@register(django.core.checks.Tags.models)
class CheckX011(ModelFieldCheck):
    ID = CheckID.X011

    def apply(
        self, field: Type[models.fields.Field], field_ast: FieldAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        if field.null is False and "null" in field_ast.kwargs:
            yield self.message(
                "Argument `null=False` is default.",
                hint="Remove `null=False` from field arguments.",
                obj=field,
            )
