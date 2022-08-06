import django.db.models
import pytest

from extra_checks.checks import model_checks, model_field_checks
from tests.example import models


@pytest.fixture
def test_case(test_case):
    return test_case.handler(model_checks.check_models)


def test_ignore_model_check(test_case):
    messages = (
        test_case.models(models.DisableCheckModel)
        .settings(
            {
                "checks": [
                    {
                        "id": model_checks.CheckModelAttribute.Id.value,
                        "attrs": ["site"],
                    },
                    model_field_checks.CheckFieldTextNull.Id.value,
                    model_checks.CheckNoUniqueTogether.Id.value,
                ]
            }
        )
        .check(
            model_checks.CheckModelAttribute,
            model_field_checks.CheckFieldTextNull,
            model_checks.CheckNoUniqueTogether,
        )
        .run()
    )
    assert not messages


def test_ignore_many_model_check(test_case):
    messages = (
        test_case.models(models.DisableManyChecksModel)
        .settings(
            {
                "checks": [
                    model_field_checks.CheckFieldTextNull.Id.value,
                    model_field_checks.CheckFieldVerboseName.Id.value,
                    model_checks.CheckNoUniqueTogether.Id.value,
                    model_checks.CheckNoIndexTogether.Id.value,
                ]
            }
        )
        .check(
            model_field_checks.CheckFieldTextNull,
            model_field_checks.CheckFieldVerboseName,
            model_checks.CheckNoUniqueTogether,
            model_checks.CheckNoIndexTogether,
        )
        .run()
    )
    assert not messages


def test_field_skipif(test_case):
    def skipif(field, *args, **kwargs):
        return isinstance(field, django.db.models.ImageField)

    messages = (
        test_case.settings(
            {
                "checks": [
                    {
                        "id": model_field_checks.CheckFieldFileUploadTo.Id.value,
                        "skipif": skipif,
                    }
                ],
            }
        )
        .models(models.ModelFieldFileUploadTo)
        .check(model_field_checks.CheckFieldFileUploadTo)
        .run()
    )
    assert len(messages) == 1
    assert {m.obj.name for m in messages} == {"file_fail"}


def test_model_skipif(test_case):
    def skipif(model, *args, **kwargs):
        return not any(
            isinstance(f, django.db.models.DateTimeField)
            for f in model._meta.get_fields()
        )

    messages = (
        test_case.settings(
            {
                "checks": [
                    {
                        "id": model_checks.CheckModelMetaAttribute.Id.value,
                        "attrs": ["get_latest_by"],
                        "skipif": skipif,
                    },
                ],
            }
        )
        .models(models.Article, models.Author)
        .check(model_checks.CheckModelMetaAttribute)
        .run()
    )
    assert len(messages) == 0
