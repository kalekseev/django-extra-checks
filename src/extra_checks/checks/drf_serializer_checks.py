import importlib
import site
from abc import abstractmethod
from typing import (
    Any,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import django.core.checks
from rest_framework.serializers import ModelSerializer, Serializer

from .. import CheckId
from ..forms import AttrsForm
from ..registry import ChecksConfig, registry
from .base_checks import BaseCheck


def _collect_serializers(
    serializers: Iterable[Type[Serializer]],
    visited: Optional[Set[Type[Serializer]]] = None,
) -> Iterator[Type[Serializer]]:
    visited = visited or set()
    for serializer in serializers:
        if serializer not in visited:
            visited.add(serializer)
            yield from _collect_serializers(serializer.__subclasses__(), visited)
            yield serializer


def _filter_app_serializers(
    serializers: Iterable[Type[Serializer]],
    include_apps: Optional[Iterable[str]] = None,
) -> Iterator[Type[Serializer]]:
    site_prefixes = set(site.PREFIXES)
    if include_apps is not None:
        app_paths = {
            a.path for a in django.apps.apps.get_app_configs() if a.name in include_apps
        }
        for s in serializers:
            module = importlib.import_module(s.__module__)
            if any(module.__file__.startswith(path) for path in app_paths):
                yield s
        return
    for s in serializers:
        module = importlib.import_module(s.__module__)
        if not any(module.__file__.startswith(path) for path in site_prefixes):
            yield s


def _get_serializers_to_check(
    include_apps: Optional[Iterable[str]] = None,
) -> Tuple[Iterator[Type[Serializer]], Iterator[Type[ModelSerializer]]]:
    serializer_classes = _filter_app_serializers(
        _collect_serializers(
            s for s in Serializer.__subclasses__() if s is not ModelSerializer
        ),
        include_apps,
    )
    model_serializer_classes = _filter_app_serializers(
        _collect_serializers(ModelSerializer.__subclasses__()), include_apps
    )
    return (
        serializer_classes,
        cast(Iterator[Type[ModelSerializer]], model_serializer_classes),
    )


@registry.add_handler("extra_checks_drf_serializer")
def check_drf_serializers(
    checks: Iterable[Union["CheckDRFSerializer", "CheckDRFModelSerializer"]],
    config: ChecksConfig,
    app_configs: Optional[List[Any]] = None,
    **kwargs: Any,
) -> Iterator[Any]:
    model_serializer_checks = []
    serializer_checks = []
    for check in checks:
        if isinstance(check, CheckDRFModelSerializer):
            model_serializer_checks.append(check)
        else:
            serializer_checks.append(check)
    s_classes, m_classes = _get_serializers_to_check(config.include_apps)
    for s in s_classes:
        for check in serializer_checks:
            yield from check(s)
    for s in m_classes:
        for check in model_serializer_checks:
            yield from check(s)


class CheckDRFSerializer(BaseCheck):
    @abstractmethod
    def apply(
        self, serializer: Serializer
    ) -> Iterator[django.core.checks.CheckMessage]:
        raise NotImplementedError()


class CheckDRFModelSerializer(BaseCheck):
    @abstractmethod
    def apply(
        self, serializer: ModelSerializer
    ) -> Iterator[django.core.checks.CheckMessage]:
        raise NotImplementedError()


@registry.register("extra_checks_drf_serializer")
class CheckDRFSerializerExtraKwargs(CheckDRFModelSerializer):
    Id = CheckId.X301
    level = django.core.checks.ERROR

    def apply(
        self, serializer: ModelSerializer
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not hasattr(serializer, "Meta") or not hasattr(
            serializer.Meta, "extra_kwargs"
        ):
            return
        invalid = serializer.Meta.extra_kwargs.keys() & serializer._declared_fields
        if invalid:
            yield self.message(
                "extra_kwargs mustn't include fields that declared on serializer.",
                hint=f"Remove extra_kwargs for fields: {', '.join(invalid)}",
                obj=serializer,
            )


@registry.register("extra_checks_drf_serializer")
class CheckDRFSerializerMetaAttribute(CheckDRFModelSerializer):
    Id = CheckId.X302
    settings_form_class = AttrsForm

    def __init__(self, attrs: List[str], **kwargs: Any) -> None:
        self.attrs = attrs
        super().__init__(**kwargs)

    def apply(
        self, serializer: ModelSerializer
    ) -> Iterator[django.core.checks.CheckMessage]:
        meta = getattr(serializer, "Meta", None)
        for attr in self.attrs:
            if not hasattr(meta, attr):
                yield self.message(
                    f"ModelSerializer must define `{attr}` in Meta.",
                    hint=f"Add `{attr}` to serializer's Meta.",
                    obj=serializer,
                )
