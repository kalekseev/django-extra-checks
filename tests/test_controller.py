from extra_checks.controller import ChecksController


def test_get_models_to_check():
    controller = ChecksController(checks={})
    assert controller.is_healthy
    models = list(controller._get_models_to_check(None))
    assert models
    for model in models:
        assert model._meta.app_label == "example"


def test_get_models_to_check_include_apps():
    controller = ChecksController(checks={}, include_apps=[])
    assert controller.is_healthy
    models = list(controller._get_models_to_check(None))
    assert not models

    controller = ChecksController(checks={}, include_apps=["django.contrib.sites"])
    assert controller.is_healthy
    models = list(controller._get_models_to_check(None))
    assert models
    for model in models:
        assert model._meta.app_label == "sites"
