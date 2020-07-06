from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Type,
    Union,
)

import django.apps
import django.core.checks
from django import forms
from django.conf import settings

from . import _IGNORED, CheckId
from .forms import ConfigForm

if TYPE_CHECKING:
    from .checks import BaseCheck


class ChecksConfig:
    def __init__(
        self,
        *,
        errors: Optional[forms.utils.ErrorDict] = None,
        checks: Optional[Dict[CheckId, dict]] = None,
        include_apps: Optional[Iterable[str]] = None,
    ) -> None:
        self.checks: Dict[CheckId, dict] = {**(checks or {}), CheckId.X001: {}}
        self.include_apps = include_apps
        self.errors = errors

    @classmethod
    def create(cls, checks: Dict["Type[BaseCheck]", Sequence[str]]) -> "ChecksConfig":
        check_forms = {r.Id: r.settings_form_class for r in checks}
        if not hasattr(settings, "EXTRA_CHECKS"):
            return cls()
        form = ConfigForm(settings.EXTRA_CHECKS)
        if not form.is_valid(check_forms):
            return cls(errors=form.errors)
        return cls(**form.cleaned_data)


_ChecksHandler = Callable[[Optional[List[Any]], Any], Iterator[Any]]


class Registry:
    def __init__(self) -> None:
        self.registered_checks: Dict["Type[BaseCheck]", Sequence[str]] = {}
        self.enabled_checks: Dict[str, List["BaseCheck"]] = {}
        self.handlers: Dict[str, _ChecksHandler] = {}
        self.is_healthy = True

    def _register(
        self, tags: List[str], check_class: "Type[BaseCheck]"
    ) -> "Type[BaseCheck]":
        self.registered_checks[check_class] = tags
        return check_class

    def _add_handler(self, tag: str, handler: _ChecksHandler) -> _ChecksHandler:
        self.handlers[tag] = handler
        return handler

    def _bind_handler(
        self,
        tag: str,
        handler: _ChecksHandler,
        checks: List["BaseCheck"],
        config: ChecksConfig,
    ) -> Optional[Callable]:
        if checks:
            f = partial(handler, checks, config)
            django.core.checks.register(f, tag)
            return f
        return None

    def register(self, *tags: str) -> Callable[["Type[BaseCheck]"], "Type[BaseCheck]"]:
        return partial(self._register, tags)

    def add_handler(self, tag: str) -> Callable[[Callable], Callable]:
        return partial(self._add_handler, tag)

    def bind(self) -> Dict[str, Callable]:
        ignored: Dict[Union[CheckId, str], set] = {}
        for obj, ids in _IGNORED.items():
            for id_ in ids:
                ignored.setdefault(id_, set()).add(obj)
        config = ChecksConfig.create(self.registered_checks)
        for check_class, tags in self.registered_checks.items():
            if check_class.Id in config.checks:
                check = check_class(
                    ignored_objects=ignored.get(check_class.Id, set()),
                    **config.checks[check_class.Id],
                )
                for tag in tags:
                    self.enabled_checks.setdefault(tag, []).append(check)
        tag_handlers = {}
        for tag, handler in self.handlers.items():
            bh = self._bind_handler(
                tag, handler, self.enabled_checks.get(tag, []), config
            )
            if bh:
                tag_handlers[tag] = bh
        self.is_healthy = not config.errors
        return tag_handlers


registry = Registry()
