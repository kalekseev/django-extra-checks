from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar, Iterator, Optional, Set, Type

import django.core.checks

from .. import CheckId, forms

MESSAGE_MAP = {
    django.core.checks.DEBUG: django.core.checks.Debug,
    django.core.checks.INFO: django.core.checks.Info,
    django.core.checks.WARNING: django.core.checks.Warning,
    django.core.checks.ERROR: django.core.checks.Error,
    django.core.checks.CRITICAL: django.core.checks.Critical,
}


class ExtraCheckMessage(django.core.checks.CheckMessage):
    def __init__(self, level, msg, hint=None, obj=None, id=None, file=None, fix=None):
        super().__init__(level, msg, hint=hint, obj=obj, id=id)
        self._file = file
        self._fix = fix


class BaseCheck(ABC):
    Id: CheckId
    settings_form_class: ClassVar[Type[forms.BaseCheckForm]] = forms.BaseCheckForm
    level = django.core.checks.WARNING

    def __init__(
        self,
        level: Optional[int] = None,
        ignore_objects: Optional[Set[Any]] = None,
        ignore_types: Optional[set] = None,
    ) -> None:
        self.level = level or self.level
        self.ignore_objects = ignore_objects or set()
        self.ignore_types = ignore_types or set()

    def __call__(
        self, obj: Any, **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        if not self.is_ignored(obj):
            yield from self.apply(obj, **kwargs)  # type: ignore

    def is_ignored(self, obj: Any) -> bool:
        return obj in self.ignore_objects or type(obj) in self.ignore_types

    def message(
        self,
        message: str,
        hint: Optional[str] = None,
        obj: Any = None,
        file: str = None,
        fix: Any = None,
    ) -> django.core.checks.CheckMessage:
        return ExtraCheckMessage(
            self.level,
            message + f" [{self.Id.value}]",
            hint=hint,
            obj=obj,
            id=self.Id.name,
            file=file,
            fix=fix,
        )


if TYPE_CHECKING:
    BaseCheckMixin = BaseCheck
else:
    BaseCheckMixin = object
