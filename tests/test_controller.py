import pytest

from extra_checks.controller import ChecksController


@pytest.fixture
def controller():
    return ChecksController(checks={})


def test_get_models_to_check(controller):
    assert controller.is_healthy
    models = list(controller._get_models_to_check(None))
    assert models
    for model in models:
        assert model._meta.app_label == "example"
