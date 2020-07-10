import pytest

from extra_checks.checks import model_checks, model_field_checks
from tests.example import models


@pytest.fixture
def test_case(test_case):
    return test_case.handler(model_checks.check_models)


def test_check_field_verbose_name(test_case):
    messages = (
        test_case.settings(
            {"checks": [model_field_checks.CheckFieldVerboseName.Id.value]}
        )
        .models(models.ModelFieldVerboseName)
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
        test_case.models(models.ModelFieldVerboseName)
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
        test_case.models(models.ModelFieldVerboseName)
        .settings(
            {"checks": [model_field_checks.CheckFieldVerboseNameGettextCase.Id.value]}
        )
        .check(model_field_checks.CheckFieldVerboseNameGettextCase)
        .run()
    )
    assert len(messages) == 1
    assert messages[0].id == model_field_checks.CheckFieldVerboseNameGettextCase.Id.name
    assert {m.obj.name for m in messages} == {
        "gettext_case",
    }


def test_check_field_null_boolean(test_case):
    messages = (
        test_case.models(models.ModelFieldNullFalse)
        .settings({"checks": [model_field_checks.CheckFieldNullBoolean.Id.value]})
        .check(model_field_checks.CheckFieldNullBoolean)
        .run()
    )
    assert len(messages) == 1
    assert messages[0].id == model_field_checks.CheckFieldNullBoolean.Id.name
    assert {m.obj.name for m in messages} == {
        "null_fail",
    }


def test_check_field_help_text_gettext(test_case):
    messages = (
        test_case.settings(
            {"checks": [model_field_checks.CheckFieldHelpTextGettext.Id.value]}
        )
        .models(models.ModelFieldHelpTextGettext)
        .check(model_field_checks.CheckFieldHelpTextGettext)
        .run()
    )
    assert len(messages) == 1
    assert messages[0].id == model_field_checks.CheckFieldHelpTextGettext.Id.name
    assert {m.obj.name for m in messages} == {
        "text_fail",
    }


def test_check_field_file_upload_to(test_case):
    messages = (
        test_case.models(models.ModelFieldFileUploadTo)
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
        .models(models.ModelFieldTextNull)
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
        .models(models.ModelFieldNullFalse)
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
        .models(models.ModelFieldForeignKeyIndex)
        .check(model_field_checks.CheckFieldForeignKeyIndex)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "article",
        "author",
    }


def test_check_field_foreign_key_index_always(test_case):
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
        .models(models.ModelFieldForeignKeyIndex)
        .check(model_field_checks.CheckFieldForeignKeyIndex)
        .run()
    )
    assert {m.obj.name for m in messages} == {
        "article",
        "author",
        "another_article",
    }


def test_generic_key_null(test_case):
    """ensure custom fields without null attribute not checked by rule"""
    (
        test_case.settings(
            {"checks": [model_field_checks.CheckFieldNullFalse.Id.value]}
        )
        .models(models.GenericKeyOne, models.GenericKeyTwo)
        .check(model_field_checks.CheckFieldNullFalse)
        .run()
    )


def test_verbose_name_of_related_field(test_case):
    """if field inherit from RelatedField the first argument is not a verbose name."""
    messages = (
        test_case.settings(
            {"checks": [model_field_checks.CheckFieldVerboseNameGettext.Id.value]}
        )
        .models(models.GenericKeyTwo)
        .check(model_field_checks.CheckFieldVerboseNameGettext)
        .run()
    )
    assert not messages


def test_field_ignore_checks(test_case, registry):
    """We must check that field.model is not in ignore_checks"""
    messages = (
        test_case.settings(
            {"checks": [model_field_checks.CheckFieldVerboseNameGettext.Id.value]}
        )
        .models(models.ModelFieldVerboseName)
        .check(model_field_checks.CheckFieldVerboseNameGettext)
        .run()
    )
    assert messages
    registry.ignore_checks(model_field_checks.CheckFieldVerboseNameGettext.Id)(
        models.ModelFieldVerboseName
    )
    messages = test_case.run()
    assert not messages


def test_field_ignore_types(test_case):
    messages = (
        test_case.settings(
            {
                "checks": [
                    {
                        "id": model_field_checks.CheckFieldFileUploadTo.Id.value,
                        "ignore_types": ["django.db.models.ImageField"],
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


def test_field_null_default_null(test_case):
    messages = (
        test_case.settings(
            {"checks": [model_field_checks.CheckFieldDefaultNull.Id.value]}
        )
        .models(models.ModelFieldNullDefault)
        .check(model_field_checks.CheckFieldDefaultNull)
        .run()
    )
    assert len(messages) == 1
    assert messages[0].obj.name == "myfield_fail"
