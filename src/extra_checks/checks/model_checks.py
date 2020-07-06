import site
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Iterator, List, Optional, Type, Union

import django.core.checks
from django import forms
from django.db import models
from django.db.models.options import DEFAULT_NAMES as META_ATTRS

from .. import CheckId
from ..ast import FieldAST, ModelAST
from ..controller import ChecksConfig, registry
from ..forms import BaseCheckForm, ListField
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
        model_ast = ModelAST(model)
        for check in model_checks:
            yield from check(model, model_ast=model_ast)
        if field_checks:
            for field, node in model_ast.field_nodes:
                field_ast = FieldAST(node)
                for check in field_checks:
                    yield from check(field, field_ast=field_ast, model=model)


class AttrsForm(BaseCheckForm):
    attrs = ListField(forms.CharField())


class MetaAttrsForm(BaseCheckForm):
    attrs = forms.MultipleChoiceField(choices=[(o, o) for o in META_ATTRS])


class CheckModel(BaseCheck):
    @abstractmethod
    def apply(
        self, model: Type[models.Model], model_ast: ModelAST
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


@registry.register(django.core.checks.Tags.models)
class CheckModelMetaAttribute(CheckModel):
    Id = CheckId.X011
    settings_form_class = MetaAttrsForm

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
