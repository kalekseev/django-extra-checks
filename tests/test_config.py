from django.core import checks

from extra_checks import CheckId
from extra_checks.checks import (
    CheckFieldFileUploadTo,
    CheckModelAttribute,
    CheckModelMetaAttribute,
)
from extra_checks.forms import ConfigForm
from extra_checks.registry import ChecksConfig
from tests.example.models import Article, Author


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


def test_config_include_apps():
    form = ConfigForm(data={"checks": []})
    assert form.is_valid({})
    assert form.cleaned_data == {"checks": {}}

    form = ConfigForm(data={"include_apps": [], "checks": []})
    assert form.is_valid({})
    assert form.cleaned_data == {"include_apps": [], "checks": {}}

    form = ConfigForm(data={"include_apps": ["tests.example"], "checks": []})
    assert form.is_valid({})
    assert form.cleaned_data == {"include_apps": ["tests.example"], "checks": {}}


def test_config_build_ignored():
    ignored, errors = ChecksConfig._build_ignored(
        {
            Article: {"X010", "random-test-name"},
            Author: {"model-meta-attribute", CheckId.X050},
        }
    )
    assert errors == [
        "Unknown check (random-test-name) provided to the 'ignore_checks'."
    ]
    assert ignored == {
        CheckId.X010: {Article},
        CheckId.X011: {Author},
        CheckId.X050: {Author},
    }
