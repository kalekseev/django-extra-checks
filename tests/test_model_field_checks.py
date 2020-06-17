import django.core.checks

from extra_checks.checks import model_field_checks
from tests.example.models import (
    ModelFieldFileUploadTo,
    ModelFieldForeignKeyIndex,
    ModelFieldNullFalse,
    ModelFieldTextNull,
    ModelFieldVerboseName,
)


def test_check_field_verbose_name(registry, use_models, settings):
    use_models(ModelFieldVerboseName)
    settings.EXTRA_CHECKS = {
        "checks": [model_field_checks.CheckFieldVerboseName.Id.value]
    }
    registry._register(
        [django.core.checks.Tags.models], model_field_checks.CheckFieldVerboseName
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert {m.obj.name for m in messages} == {
        "no_name",
        "no_name_related",
        "no_name_nested_field",
    }


def test_check_field_verbose_name_gettext(registry, use_models, settings):
    use_models(ModelFieldVerboseName)
    settings.EXTRA_CHECKS = {
        "checks": [model_field_checks.CheckFieldVerboseNameGettext.Id.value]
    }
    registry._register(
        [django.core.checks.Tags.models],
        model_field_checks.CheckFieldVerboseNameGettext,
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert {m.obj.name for m in messages} == {
        "first_arg_name",
        "kwarg_name",
        "gettext",
        "name_related",
        "nested_field",
    }


def test_check_field_verbose_name_gettext_case(registry, use_models, settings):
    use_models(ModelFieldVerboseName)
    settings.EXTRA_CHECKS = {
        "checks": [model_field_checks.CheckFieldVerboseNameGettextCase.Id.value]
    }
    registry._register(
        [django.core.checks.Tags.models],
        model_field_checks.CheckFieldVerboseNameGettextCase,
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert {m.obj.name for m in messages} == {
        "gettext_case",
    }


def test_check_field_file_upload_to(registry, use_models, settings):
    use_models(ModelFieldFileUploadTo)
    settings.EXTRA_CHECKS = {
        "checks": [model_field_checks.CheckFieldFileUploadTo.Id.value]
    }
    registry._register(
        [django.core.checks.Tags.models], model_field_checks.CheckFieldFileUploadTo,
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert {m.obj.name for m in messages} == {
        "image_fail",
        "file_fail",
    }


def test_check_field_text_null(registry, use_models, settings):
    use_models(ModelFieldTextNull)
    settings.EXTRA_CHECKS = {"checks": [model_field_checks.CheckFieldTextNull.Id.value]}
    registry._register(
        [django.core.checks.Tags.models], model_field_checks.CheckFieldTextNull,
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert {m.obj.name for m in messages} == {
        "text_fail",
        "chars_fail",
        "custom_fail",
    }


def test_check_field_null_false(registry, use_models, settings):
    use_models(ModelFieldNullFalse)
    settings.EXTRA_CHECKS = {
        "checks": [model_field_checks.CheckFieldNullFalse.Id.value]
    }
    registry._register(
        [django.core.checks.Tags.models], model_field_checks.CheckFieldNullFalse,
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert {m.obj.name for m in messages} == {
        "myfield_fail",
    }


def test_check_field_foreign_key_index(registry, use_models, settings):
    use_models(ModelFieldForeignKeyIndex)
    settings.EXTRA_CHECKS = {
        "checks": [model_field_checks.CheckFieldForeignKeyIndex.Id.value]
    }
    registry._register(
        [django.core.checks.Tags.models], model_field_checks.CheckFieldForeignKeyIndex,
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert {m.obj.name for m in messages} == {
        "article",
        "author",
    }


def test_check_field_foreign_key_index_always(registry, use_models, settings):
    use_models(ModelFieldForeignKeyIndex)
    settings.EXTRA_CHECKS = {
        "checks": [
            {
                "id": model_field_checks.CheckFieldForeignKeyIndex.Id.value,
                "when": "always",
            }
        ]
    }
    registry._register(
        [django.core.checks.Tags.models], model_field_checks.CheckFieldForeignKeyIndex,
    )
    controller = registry.finish()
    assert controller.is_healthy
    messages = list(controller.check_models())
    assert {m.obj.name for m in messages} == {
        "article",
        "author",
        "another_article",
    }
