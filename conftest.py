import pytest

from extra_checks.checks.self_checks import CheckConfig
from extra_checks.controller import Registry


@pytest.fixture
def registry() -> Registry:
    registry = Registry()
    registry._register(["extra_checks_selfcheck"], CheckConfig)
    return registry


@pytest.fixture
def use_models(monkeypatch):
    def f(*models):
        monkeypatch.setattr(
            "extra_checks.controller.ChecksController._get_models_to_check",
            lambda *a: (m for m in models),
        )

    return f
