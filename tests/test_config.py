from django.core import checks

from extra_checks import CheckId, ignore_checks
from extra_checks.checks import (
    CheckFieldFileUploadTo,
    CheckModelAttribute,
    CheckModelMetaAttribute,
)
from extra_checks.controller import ChecksController
from extra_checks.forms import ConfigForm


def test_config_form():
    form = ConfigForm(
        data={
            "checks": [
                {
                    "id": CheckModelAttribute.Id.value,
                    "level": "WARNING",
                    "attrs": ["db_table"],
                }
            ]
        }
    )
    assert form.is_valid(
        {CheckModelAttribute.Id: CheckModelAttribute.settings_form_class}
    )
    assert form.cleaned_data == {
        "checks": {
            CheckModelAttribute.Id.value: {
                "level": checks.WARNING,
                "attrs": ["db_table"],
            }
        },
    }

    form = ConfigForm(data={"checks": [CheckFieldFileUploadTo.Id.value]})
    assert form.is_valid(
        {CheckFieldFileUploadTo.Id: CheckFieldFileUploadTo.settings_form_class}
    )
    assert form.cleaned_data == {
        "checks": {CheckFieldFileUploadTo.Id.value: {"level": None}},
    }

    form = ConfigForm(data={})
    assert form.is_valid({})
    assert form.cleaned_data == {"checks": {}}

    form = ConfigForm(
        data={"checks": [{"id": CheckModelAttribute.Id.value, "attrs": ["db_table"]}]}
    )
    assert form.is_valid(
        {CheckModelAttribute.Id: CheckModelAttribute.settings_form_class}
    )
    assert form.cleaned_data == {
        "checks": {
            CheckModelAttribute.Id.value: {"level": None, "attrs": ["db_table"]}
        },
    }

    form = ConfigForm(data={"checks": [{5}]})
    assert not form.is_valid(
        {CheckModelAttribute.Id: CheckModelAttribute.settings_form_class}
    )
    assert form.errors == {
        "checks": ["{5} is not one of the available types."],
    }

    form = ConfigForm(data={"checks": CheckModelAttribute.Id.value})
    assert not form.is_valid(
        {CheckModelAttribute.Id: CheckModelAttribute.settings_form_class}
    )
    assert form.errors == {
        "checks": ["Enter a list of values."],
    }

    form = ConfigForm(data={"checks": ["X000"]})
    assert not form.is_valid(
        {CheckFieldFileUploadTo.Id: CheckFieldFileUploadTo.settings_form_class}
    )
    assert form.errors == {"checks": ["X000 is not one of the available checks."]}

    form = ConfigForm(
        data={
            "checks": [
                {
                    "id": CheckModelMetaAttribute.Id.value,
                    "level": "FAKE",
                    "attrs": ["random"],
                }
            ]
        }
    )
    assert not form.is_valid(
        {CheckModelMetaAttribute.Id: CheckModelMetaAttribute.settings_form_class}
    )
    assert form.errors == {
        "checks": {
            CheckModelMetaAttribute.Id.value: {
                "attrs": [
                    "Select a valid choice. random is not one of the available choices."
                ],
                "level": [
                    "Select a valid choice. FAKE is not one of the available choices."
                ],
            },
        }
    }


def test_controller(settings):
    controller = ChecksController.create(checks={CheckFieldFileUploadTo: ["tag"]})
    assert controller.is_healthy

    settings.EXTRA_CHECKS = {"checks": [CheckFieldFileUploadTo.Id.value]}
    controller = ChecksController.create(checks={CheckFieldFileUploadTo: ["tag"]})
    assert not controller.errors
    assert controller.is_healthy
    assert len(controller.registered_checks["tag"]) == 1
    check = controller.registered_checks["tag"][0]
    assert isinstance(check, CheckFieldFileUploadTo)


def test_ignore_checks(monkeypatch):
    ignore: dict = {}
    monkeypatch.setattr("extra_checks._IGNORED", ignore)
    obj = object()
    res = ignore_checks("X010", "model-attribute", CheckId.X050)(obj)
    assert res == obj
    assert ignore == {obj: {"X010", "model-attribute", CheckId.X050}}
