import site
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Type,
)

import django.apps
import django.core.checks
from django import forms
from django.conf import settings

from . import _IGNORED, CheckID
from .ast import FieldAST, ModelAST
from .forms import ConfigForm

if TYPE_CHECKING:
    from .checks import Check


DEFAULT_CONFIG: dict = {
    "checks": [],
}


class Registry:
    def __init__(self) -> None:
        self.checks: Dict["Type[Check]", Sequence[str]] = {}

    def register(self, *tags: str) -> Callable[["Type[Check]"], "Type[Check]"]:
        def inner(check_class: "Type[Check]") -> "Type[Check]":
            self.checks[check_class] = tags
            return check_class

        return inner

    def finish(self) -> None:
        controller = ChecksController.create(self.checks)

        def f(callback: Callable) -> Callable:
            def inner(*args: Any, **kwargs: Any) -> Any:
                return callback(*args, **kwargs)

            return inner

        django.core.checks.register(
            f(controller.check_extra_checks_health), "extra_checks_health"
        )
        django.core.checks.register(
            f(controller.check_models), django.core.checks.Tags.models
        )


class ChecksController:
    def __init__(
        self,
        checks: Dict["Type[Check]", Sequence[str]],
        config: Dict[CheckID, dict] = None,
        errors: forms.utils.ErrorDict = None,
    ) -> None:
        checks = checks or {}
        config = config or {CheckID.X001: {}}
        self.errors = errors
        self.registered_checks: Dict[str, List["Check"]] = {}
        self.ignored: Dict[CheckID, set] = {}
        for obj, ids in _IGNORED.items():
            for id_ in ids:
                self.ignored.setdefault(id_, set()).add(obj)
        for check_class, tags in checks.items():
            if check_class.ID in config:
                check = check_class(
                    ignored_objects=self.ignored.get(check_class.ID, set()),
                    **config[check_class.ID],
                )
                for tag in tags:
                    self.registered_checks.setdefault(tag, []).append(check)

    @classmethod
    def create(cls, checks: Dict["Type[Check]", Sequence[str]]) -> "ChecksController":
        check_form = {r.ID: r.settings_form_class for r in checks}
        if not hasattr(settings, "EXTRA_CHECKS"):
            return cls(checks=checks)
        form = ConfigForm(settings.EXTRA_CHECKS)  # type: ignore
        if form.is_valid(check_form):
            return cls(checks=checks, config=form.cleaned_data["checks"])
        return cls(checks=checks, errors=form.errors)

    @property
    def is_healthy(self) -> bool:
        return not self.errors

    def check_extra_checks_health(
        self, app_configs: Optional[List[Any]], **kwargs: Any
    ) -> Iterator[django.core.checks.CheckMessage]:
        for check in self.registered_checks.get("extra_checks_health", []):
            yield from check(self)

    def check_models(
        self, app_configs: Optional[List[Any]], **kwargs: Any
    ) -> Iterator[Any]:
        apps = (
            django.apps.apps.get_app_configs() if app_configs is None else app_configs
        )
        site_prefixes = set(site.PREFIXES)
        for app in apps:
            if not any(app.path.startswith(path) for path in site_prefixes):
                for model in app.get_models():
                    model_ast = ModelAST(model)
                    for check in self.registered_checks.get(
                        django.core.checks.Tags.models, []
                    ):
                        yield from check(model, model_ast=model_ast)
                    extra_checks_model_fields = self.registered_checks.get(
                        "extra_checks_model_fields", []
                    )
                    if extra_checks_model_fields:
                        for field, node in model_ast.field_nodes:
                            field_ast = FieldAST(node)
                            for check in extra_checks_model_fields:
                                yield from check(field, field_ast=field_ast)


registry = Registry()
register = registry.register
