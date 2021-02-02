import site
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Iterator, List, Optional, Type, Union

import django.core.checks
from django import forms
from django.apps import apps
from django.contrib.admin.sites import all_sites
from django.db import models
from django.db.models.options import DEFAULT_NAMES as META_ATTRS

from .. import CheckId
from ..ast import ModelASTProtocol, get_model_ast
from ..forms import AttrsForm, BaseCheckForm
from ..registry import ChecksConfig, registry
from .base_checks import BaseCheck

if TYPE_CHECKING:
    from .model_field_checks import CheckModelField


def _get_models_to_check(
    *,
    app_configs: Optional[List[Any]] = None,
    include_apps: Optional[Iterable[str]] = None,
) -> Iterator[Type[models.Model]]:
    apps = django.apps.apps.get_app_configs() if app_configs is None else app_configs
    if include_apps is not None:
        for app in apps:
            if app.name in include_apps:
                yield from app.get_models()
        return
    for app in apps:
        if not any(app.path.startswith(path) for path in set(site.PREFIXES)):
            yield from app.get_models()


@registry.add_handler(django.core.checks.Tags.models)
def check_models(
    checks: Iterable[Union["CheckModel", "CheckModelField"]],
    config: ChecksConfig,
    app_configs: Optional[List[Any]] = None,
    **kwargs: Any,
) -> Iterator[Any]:
    model_checks = []
    field_checks = []
    for check in checks:
        if isinstance(check, CheckModel):
            model_checks.append(check)
        else:
            field_checks.append(check)
    if not model_checks and not field_checks:
        return
    for model in _get_models_to_check(
        app_configs=app_configs, include_apps=config.include_apps
    ):
        model_ast = get_model_ast(model)
        for check in model_checks:
            yield from check(model, ast=model_ast)
        if field_checks:
            for field, field_ast in model_ast.field_nodes:
                for check in field_checks:
                    yield from check(field, ast=field_ast, model=model)


class CheckModel(BaseCheck):
    @abstractmethod
    def apply(
        self, model: Type[models.Model], ast: ModelASTProtocol
    ) -> Iterator[django.core.checks.CheckMessage]:
        raise NotImplementedError()


@registry.register(django.core.checks.Tags.models)
class CheckModelAttribute(CheckModel):
    Id = CheckId.X010
    settings_form_class = AttrsForm

    def __init__(self, attrs: List[str], **kwargs: Any) -> None:
        self.attrs = attrs
        super().__init__(**kwargs)

    def apply(
        self, model: Type[models.Model], ast: ModelASTProtocol
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


@registry.register(django.core.checks.Tags.models)
class CheckModelMetaAttribute(CheckModel):
    Id = CheckId.X011

    class MetaAttrsForm(BaseCheckForm):
        attrs = forms.MultipleChoiceField(choices=[(o, o) for o in META_ATTRS])

    settings_form_class = MetaAttrsForm

    def __init__(self, attrs: List[str], **kwargs: Any) -> None:
        self.attrs = attrs
        super().__init__(**kwargs)

    def apply(
        self, model: Type[models.Model], ast: ModelASTProtocol
    ) -> Iterator[django.core.checks.CheckMessage]:
        for attr in self.attrs:
            if (
                not model._meta.abstract
                and not model._meta.proxy
                and not ast.has_meta_var(attr)
            ):
                yield self.message(
                    f'Each model must specify "{attr}" attribute in its Meta.',
                    hint=f'Set "{attr}" attribute in Meta.',
                    obj=model,
                )


@registry.register(django.core.checks.Tags.models)
class CheckModelAdmin(CheckModel):
    Id = CheckId.X012

    class AdminForm(BaseCheckForm):
        def clean(self) -> dict:
            if not apps.is_installed("django.contrib.admin"):
                raise forms.ValidationError(
                    "django.contrib.admin must be in INSTALLED_APPS."
                )
            return super().clean()

    settings_form_class = AdminForm

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.models_with_admin = set()
        for admin_site in all_sites:
            for model_cls, admin_cls in admin_site._registry.items():
                self.models_with_admin.add(model_cls)
                for inline in admin_cls.inlines:
                    self.models_with_admin.add(inline.model)

    def apply(
        self, model: Type[models.Model], ast: ModelASTProtocol
    ) -> Iterator[django.core.checks.CheckMessage]:
        if model not in self.models_with_admin:
            yield self.message("The model is not registered in admin.", obj=model)


@registry.register(django.core.checks.Tags.models)
class CheckNoUniqueTogether(CheckModel):
    Id = CheckId.X013

    def apply(
        self, model: Type[models.Model], ast: ModelASTProtocol
    ) -> Iterator[django.core.checks.CheckMessage]:
        if ast.has_meta_var("unique_together"):
            yield self.message(
                "Use UniqueConstraint with the constraints option instead.",
                obj=model,
            )


@registry.register(django.core.checks.Tags.models)
class CheckNoIndexTogether(CheckModel):
    Id = CheckId.X014

    def apply(
        self, model: Type[models.Model], ast: ModelASTProtocol
    ) -> Iterator[django.core.checks.CheckMessage]:
        if ast.has_meta_var("index_together"):
            yield self.message("Use the indexes option instead", obj=model)
