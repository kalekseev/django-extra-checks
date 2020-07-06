import pytest

from extra_checks.checks import model_checks, model_field_checks
from tests.example.models import (
    ModelFieldFileUploadTo,
    ModelFieldForeignKeyIndex,
    ModelFieldNullFalse,
    ModelFieldTextNull,
    ModelFieldVerboseName,
)


@pytest.fixture
def test_case(test_case):
    return test_case.handler(model_checks.check_models)


def test_check_field_verbose_name(test_case):
    messages = (
        test_case.settings(
            {"checks": [model_field_checks.CheckFieldVerboseName.Id.value]}
        )
        .models(ModelFieldVerboseName)
        .check(model_field_checks.CheckFieldVerboseName)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "no_name",
        "no_name_related",
        "no_name_nested_field",
    }


def test_check_field_verbose_name_gettext(test_case):
    messages = (
        test_case.models(ModelFieldVerboseName)
        .settings(
            {"checks": [model_field_checks.CheckFieldVerboseNameGettext.Id.value]}
        )
        .check(model_field_checks.CheckFieldVerboseNameGettext)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "first_arg_name",
        "kwarg_name",
        "gettext",
        "name_related",
        "nested_field",
    }


def test_check_field_verbose_name_gettext_case(test_case):
    messages = (
        test_case.models(ModelFieldVerboseName)
        .settings(
            {"checks": [model_field_checks.CheckFieldVerboseNameGettextCase.Id.value]}
        )
        .check(model_field_checks.CheckFieldVerboseNameGettextCase)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "gettext_case",
    }


def test_check_field_file_upload_to(test_case):
    messages = (
        test_case.models(ModelFieldFileUploadTo)
        .settings({"checks": [model_field_checks.CheckFieldFileUploadTo.Id.value]})
        .check(model_field_checks.CheckFieldFileUploadTo)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "image_fail",
        "file_fail",
    }


def test_check_field_text_null(test_case):
    messages = (
        test_case.settings({"checks": [model_field_checks.CheckFieldTextNull.Id.value]})
        .models(ModelFieldTextNull)
        .check(model_field_checks.CheckFieldTextNull)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "text_fail",
        "chars_fail",
        "custom_fail",
    }


def test_check_field_null_false(test_case):
    messages = (
        test_case.settings(
            {"checks": [model_field_checks.CheckFieldNullFalse.Id.value]}
        )
        .models(ModelFieldNullFalse)
        .check(model_field_checks.CheckFieldNullFalse)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "myfield_fail",
    }


def test_check_field_foreign_key_index(test_case):
    messages = (
        test_case.settings(
            {"checks": [model_field_checks.CheckFieldForeignKeyIndex.Id.value]}
        )
        .models(ModelFieldForeignKeyIndex)
        .check(model_field_checks.CheckFieldForeignKeyIndex)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "article",
        "author",
    }


def test_check_field_foreign_key_index_always(registry, test_case, settings):
    settings = {
        "checks": [
            {
                "id": model_field_checks.CheckFieldForeignKeyIndex.Id.value,
                "when": "always",
            }
        ]
    }
    messages = (
        test_case.settings(settings)
        .models(ModelFieldForeignKeyIndex)
        .check(model_field_checks.CheckFieldForeignKeyIndex)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "article",
        "author",
        "another_article",
    }
