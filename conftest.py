import pytest

from extra_checks.checks.self_checks import CheckConfig
from extra_checks.controller import Registry


@pytest.fixture
def registry() -> Registry:
    registry = Registry()
    registry._register(["extra_checks_selfcheck"], CheckConfig)
    return registry


class TestCase:
    TEST_TAG = "__test_case_check__"

    def __init__(self, settings, monkeypatch, registry):
        self._settings = settings
        self._monkeypatch = monkeypatch
        self._registry = registry

    def settings(self, settings):
        self._settings.EXTRA_CHECKS = settings
        return self

    def models(self, *models):
        self._monkeypatch.setattr(
            "extra_checks.checks.model_checks._get_models_to_check",
            lambda *a, **kw: (m for m in models),
        )
        return self

    def check(self, check):
        self._registry._register([self.TEST_TAG], check)
        return self

    def handler(self, handler):
        self._registry._add_handler(self.TEST_TAG, handler)
        return self

    def run(self):
        assert self._registry.is_healthy
        self._registry.enabled_checks = {}
        handlers = self._registry.bind()
        return list(handlers[self.TEST_TAG]())


@pytest.fixture
def test_case(settings, monkeypatch, registry):
    return TestCase(settings, monkeypatch, registry)
