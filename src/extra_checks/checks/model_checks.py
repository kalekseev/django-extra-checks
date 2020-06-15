from abc import abstractmethod
from typing import Any, Iterator, List, Type

import django.core.checks
from django.db import models

from .. import CheckId, forms
from ..ast import ModelAST
from ..controller import register
from .base_checks import BaseCheck


class ModelCheck(BaseCheck):
    @abstractmethod
    def apply(
        self, model: Type[models.Model], model_ast: ModelAST
    ) -> Iterator[django.core.checks.CheckMessage]:
        raise NotImplementedError()


@register(django.core.checks.Tags.models)
class CheckModelAttribute(ModelCheck):
    Id = CheckId.X010
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
class CheckModelMetaAttribute(ModelCheck):
    Id = CheckId.X011
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
