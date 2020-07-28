import pytest

from extra_checks.checks import model_checks
from tests.example.models import (
    Article,
    Author,
    ModelFieldForeignKeyIndex,
    ModelFieldTextNull,
)


@pytest.fixture
def test_case(test_case):
    return test_case.handler(model_checks.check_models)


def test_get_models_to_check():
    models = list(model_checks._get_models_to_check())
    assert models
    for model in models:
        assert model._meta.app_label == "example"


def test_get_models_to_check_include_apps():
    models = list(model_checks._get_models_to_check(include_apps=[]))
    assert not models

    models = list(
        model_checks._get_models_to_check(include_apps=["django.contrib.sites"])
    )
    assert models
    for model in models:
        assert model._meta.app_label == "sites"


def test_check_model_attrs(test_case):
    messages = (
        test_case.models(Article)
        .settings(
            {
                "checks": [
                    {"id": model_checks.CheckModelAttribute.Id.value, "attrs": ["site"]}
                ]
            }
        )
        .check(model_checks.CheckModelAttribute)
        .run()
    )
    assert not messages
    messages = test_case.models(Author).run()
    assert len(messages) == 1
    assert messages[0].id == model_checks.CheckModelAttribute.Id.name


def test_check_model_meta_attrs(test_case):
    messages = (
        test_case.models(Article)
        .settings(
            {
                "checks": [
                    {
                        "id": model_checks.CheckModelMetaAttribute.Id.value,
                        "attrs": ["verbose_name"],
                    }
                ]
            }
        )
        .check(model_checks.CheckModelMetaAttribute)
        .run()
    )
    assert not messages
    messages = test_case.models(Author).run()
    assert len(messages) == 1
    assert messages[0].id == model_checks.CheckModelMetaAttribute.Id.name


def test_admin_models(test_case):
    messages = (
        test_case.models(Article, Author)
        .settings({"checks": [model_checks.CheckModelAdmin.Id.value]})
        .check(model_checks.CheckModelAdmin)
        .run()
    )
    assert not messages
    messages = test_case.models(ModelFieldTextNull).run()
    assert len(messages) == 1
    assert messages[0].id == model_checks.CheckModelAdmin.Id.name


def test_no_unique_together(test_case):
    messages = (
        test_case.models(ModelFieldForeignKeyIndex)
        .settings({"checks": [model_checks.CheckNoUniqueTogether.Id.value]})
        .check(model_checks.CheckNoUniqueTogether)
        .run()
    )
    assert len(messages) == 1
    assert messages[0].id == model_checks.CheckNoUniqueTogether.Id.name


def test_no_index_together(test_case):
    messages = (
        test_case.models(ModelFieldForeignKeyIndex)
        .settings({"checks": [model_checks.CheckNoIndexTogether.Id.value]})
        .check(model_checks.CheckNoIndexTogether)
        .run()
    )
    assert len(messages) == 1
    assert messages[0].id == model_checks.CheckNoIndexTogether.Id.name
