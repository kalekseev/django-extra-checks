from abc import ABC
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Iterator, Optional, Set, Type

import django.core.checks

from .. import CheckId, forms
from ..ast.protocols import DisableCommentProtocol

MESSAGE_MAP = {
    django.core.checks.DEBUG: django.core.checks.Debug,
    django.core.checks.INFO: django.core.checks.Info,
    django.core.checks.WARNING: django.core.checks.Warning,
    django.core.checks.ERROR: django.core.checks.Error,
    django.core.checks.CRITICAL: django.core.checks.Critical,
}


class BaseCheck(ABC):
    Id: CheckId
    settings_form_class: ClassVar[Type[forms.BaseCheckForm]] = forms.BaseCheckForm
    level = django.core.checks.WARNING

    def __init__(
        self,
        level: Optional[int] = None,
        ignore_objects: Optional[Set[Any]] = None,
        ignore_types: Optional[set] = None,
        skipif: Optional[Callable] = None,
    ) -> None:
        self.level = level or self.level
        self.ignore_objects = ignore_objects or set()
        self.ignore_types = ignore_types or set()
        self.skipif = skipif

    def __call__(
        self, obj: Any, ast: Optional[DisableCommentProtocol] = None, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not self.is_ignored(obj):
            for error in self.apply(obj, ast=ast, **kwargs):  # type: ignore
                if not ast or not ast.is_disabled_by_comment(error.id):
                    yield error

    def is_ignored(self, obj: Any) -> bool:
        if self.skipif and self.skipif(obj):
            return True
        return obj in self.ignore_objects or type(obj) in self.ignore_types

    def message(
        self, message: str, hint: Optional[str] = None, obj: Any = None
    ) -> django.core.checks.CheckMessage:
        return MESSAGE_MAP[self.level](
            message + f" [{self.Id.value}]", hint=hint, obj=obj, id=self.Id.name
        )


if TYPE_CHECKING:
    BaseCheckMixin = BaseCheck
else:
    BaseCheckMixin = object
