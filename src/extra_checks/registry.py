from collections.abc import Iterable, Iterator, Sequence
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Union,
)

import django.apps
import django.core.checks
from django.conf import settings

from . import CheckId
from .forms import ConfigForm

if TYPE_CHECKING:
    from .checks import BaseCheck


class ChecksConfig:
    def __init__(
        self,
        *,
        errors: Optional[dict] = None,
        checks: Optional[dict[CheckId, dict]] = None,
        include_apps: Optional[Iterable[str]] = None,
        ignored_objects: Optional[dict[CheckId, set[Any]]] = None,
    ) -> None:
        self.checks: dict[CheckId, dict] = {**(checks or {}), CheckId.X001: {}}
        self.include_apps = include_apps
        self.errors = errors
        self.ignored_objects: dict[CheckId, set] = ignored_objects or {}

    @classmethod
    def create(
        cls,
        include_checks: dict["type[BaseCheck]", Sequence[str]],
        ignore_checks: Optional[dict[Any, set[Union[str, CheckId]]]] = None,
    ) -> "ChecksConfig":
        check_forms = {r.Id: r.settings_form_class for r in include_checks}
        if not hasattr(settings, "EXTRA_CHECKS"):
            return cls()
        form = ConfigForm(settings.EXTRA_CHECKS)
        if not form.is_valid(check_forms):
            return cls(errors=form.errors)
        ignored, errors = ChecksConfig._build_ignored(ignore_checks or {})
        if errors:
            return cls(errors={"__all__": errors})
        return cls(ignored_objects=ignored, **form.cleaned_data)

    @staticmethod
    def _build_ignored(
        ignore_checks: dict[Any, set[Union[str, CheckId]]],
    ) -> tuple[dict[CheckId, set[Any]], list[str]]:
        errors = []
        ignored: dict[CheckId, set] = {}
        for obj, ids in ignore_checks.items():
            for id_ in ids:
                check_id = CheckId.find_check(id_)
                if check_id:
                    ignored.setdefault(check_id, set()).add(obj)
                else:
                    errors.append(
                        f"Unknown check ({id_}) provided to the 'ignore_checks'."
                    )
        return ignored, errors


_ChecksHandler = Callable[[Optional[list[Any]], Any], Iterator[Any]]


class Registry:
    def __init__(self) -> None:
        self.registered_checks: dict[type[BaseCheck], Sequence[str]] = {}
        self.enabled_checks: dict[str, list[BaseCheck]] = {}
        self.ignored_checks: dict[Any, set[Union[CheckId, str]]] = {}
        self.handlers: dict[str, _ChecksHandler] = {}
        self._config: Optional[ChecksConfig] = None

    def _register(
        self, tags: Sequence[str], check_class: "type[BaseCheck]"
    ) -> "type[BaseCheck]":
        self.registered_checks[check_class] = tags
        return check_class

    def _add_handler(self, tag: str, handler: _ChecksHandler) -> _ChecksHandler:
        self.handlers[tag] = handler
        return handler

    def _bind_handler(
        self,
        tag: str,
        handler: _ChecksHandler,
        checks: list["BaseCheck"],
        config: ChecksConfig,
    ) -> Optional[Callable]:
        if checks:
            f = partial(handler, checks, config)
            django.core.checks.register(f, tag)  # pyright: ignore
            return f
        return None

    def register(self, *tags: str) -> Callable[["type[BaseCheck]"], "type[BaseCheck]"]:
        return partial(self._register, tags)

    def add_handler(self, tag: str) -> Callable[[Callable], Callable]:
        return partial(self._add_handler, tag)

    def bind(self) -> dict[str, Callable]:
        config = ChecksConfig.create(self.registered_checks, self.ignored_checks)
        for check_class, tags in self.registered_checks.items():
            if check_class.Id in config.checks:
                check = check_class(
                    ignore_objects=config.ignored_objects.get(check_class.Id, set()),
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
        self._config = config
        return tag_handlers

    @property
    def is_healthy(self) -> bool:
        return True if self._config is None else not self._config.errors


registry = Registry()
