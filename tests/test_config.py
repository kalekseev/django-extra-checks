from django.core import checks

from extra_checks.checks import CheckX002, CheckX004
from extra_checks.controller import ChecksController
from extra_checks.forms import ConfigForm


def test_config_form():
    form = ConfigForm(
        data={"checks": [{"id": "X002", "level": "WARNING", "attrs": ["db_table"]}]}
    )
    assert form.is_valid({CheckX002.ID: CheckX002.settings_form_class})
    assert form.cleaned_data == {
        "checks": {"X002": {"level": checks.WARNING}},
    }

    form = ConfigForm(data={"checks": ["X002"]})
    assert form.is_valid({CheckX002.ID: CheckX002.settings_form_class})
    assert form.cleaned_data == {
        "checks": {"X002": {"level": None}},
    }

    form = ConfigForm(data={})
    assert form.is_valid({})
    assert form.cleaned_data == {"checks": {}}

    form = ConfigForm(data={"checks": [{"id": "X002", "attrs": ["db_table"]}]})
    assert form.is_valid({CheckX002.ID: CheckX002.settings_form_class})
    assert form.cleaned_data == {
        "checks": {"X002": {"level": None}},
    }

    form = ConfigForm(data={"checks": [{5}]})
    assert not form.is_valid({CheckX002.ID: CheckX002.settings_form_class})
    assert form.errors == {
        "checks": ["{5} is not one of the available types."],
    }

    form = ConfigForm(data={"checks": "X002"})
    assert not form.is_valid({CheckX002.ID: CheckX002.settings_form_class})
    assert form.errors == {
        "checks": ["Enter a list of values."],
    }

    form = ConfigForm(data={"checks": ["X000"]})
    assert not form.is_valid({CheckX004.ID: CheckX004.settings_form_class})
    assert form.errors == {"checks": ["X000 is not one of the available checks."]}

    form = ConfigForm(
        data={"checks": [{"id": "X004", "level": "FAKE", "attrs": ["random"]}]}
    )
    assert not form.is_valid({CheckX004.ID: CheckX004.settings_form_class})
    assert form.errors == {
        "checks": {
            "X004": {
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
    controller = ChecksController.create(checks={CheckX004: ["tag"]})
    assert controller.is_healthy

    settings.EXTRA_CHECKS = {"checks": ["X002"]}
    controller = ChecksController.create(checks={CheckX002: ["tag"]})
    assert not controller.errors
    assert controller.is_healthy
    assert len(controller.registered_checks["tag"]) == 1
    check = controller.registered_checks["tag"][0]
    assert isinstance(check, CheckX002)
