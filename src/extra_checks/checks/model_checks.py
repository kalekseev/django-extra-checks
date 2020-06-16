from abc import abstractmethod
from typing import Any, Iterator, List, Type

import django.core.checks
from django import forms
from django.db import models
from django.db.models.options import DEFAULT_NAMES as META_ATTRS

from .. import CheckId
from ..ast import ModelAST
from ..controller import register
from ..forms import BaseCheckForm, ListField
from .base_checks import BaseCheck


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


@register(django.core.checks.Tags.models)
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


@register(django.core.checks.Tags.models)
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
