import importlib
import typing

import django.core.checks
from django import forms
from django.utils.translation import gettext_lazy as _

from . import CheckId


class ListField(forms.Field):
    default_error_messages = {
        "invalid_list": _("Enter a list of values."),
    }

    def __init__(self, base_field: forms.Field, **kwargs: typing.Any) -> None:
        self.base_field = base_field
        super().__init__(**kwargs)

    def to_python(self, value: typing.Any) -> list:
        if not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise forms.ValidationError(
                self.error_messages["invalid_list"], code="invalid_list"
            )
        return [self.base_field.to_python(val) for val in value]

    def validate(self, value: list) -> None:
        if self.required and not value:
            raise forms.ValidationError(
                self.error_messages["required"], code="required"
            )
        for val in value:
            self.base_field.validate(val)


class UnionField(forms.Field):
    default_error_messages = {
        "type_invalid": _("%(value)s is not one of the available types."),
    }

    def __init__(
        self, base_fields: typing.Dict[typing.Any, forms.Field], **kwargs: typing.Any
    ) -> None:
        assert isinstance(base_fields, dict)
        self.base_fields = base_fields
        super().__init__(**kwargs)

    def to_python(self, value: typing.Any) -> typing.Any:
        for type_, field in self.base_fields.items():
            if isinstance(value, type_):
                return field.to_python(value)
        raise forms.ValidationError(
            self.error_messages["type_invalid"],
            code="type_invalid",
            params={"value": value},
        )

    def validate(self, value: typing.Any) -> None:
        for type_, field in self.base_fields.items():
            if isinstance(value, type_):
                field.validate(value)
                return


class DictField(forms.ChoiceField):
    default_error_messages = {
        "invalid_choice": _("ID %(value)s is not one of the available checks."),
        "invalid_dict": _("Must be a dict."),
        "id_required": _("`id` field is required."),
    }

    def __init__(
        self, id_choices: typing.List[typing.Tuple[str, str]], **kwargs: typing.Any
    ) -> None:
        super().__init__(choices=id_choices, **kwargs)

    def to_python(self, value: typing.Any) -> dict:
        if not value:
            return {}
        if not isinstance(value, dict):
            raise forms.ValidationError(
                self.error_messages["invalid_dict"], code="invalid_dict",
            )
        return {str(k): v for k, v in value.items()}

    def validate(self, value: dict) -> None:
        if self.required and not value:
            raise forms.ValidationError(
                self.error_messages["required"], code="required"
            )
        if "id" not in value:
            raise forms.ValidationError(
                self.error_messages["id_required"], code="id_required"
            )
        if not self.valid_value(value["id"]):
            raise forms.ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value["id"]},
            )


class ConfigForm(forms.Form):
    include_apps = ListField(forms.CharField(), required=False)
    checks = ListField(
        UnionField(
            {
                str: forms.ChoiceField(
                    choices=[(v.value, v.value) for v in CheckId.__members__.values()],
                    error_messages={
                        "invalid_choice": _(
                            "%(value)s is not one of the available checks."
                        ),
                    },
                ),
                dict: DictField(
                    id_choices=[
                        (v.value, v.value) for v in CheckId.__members__.values()
                    ]
                ),
            }
        ),
        required=False,
    )

    def clean_checks(self) -> typing.Dict[str, dict]:
        result: typing.Dict[str, dict] = {}
        for check in self.cleaned_data["checks"]:
            if isinstance(check, str):
                result[check] = {}
            else:
                result[check["id"]] = check
        return result

    def clean(self) -> typing.Dict[str, typing.Any]:
        if (
            "include_apps" in self.cleaned_data
            and not self.cleaned_data["include_apps"]
            and "include_apps" not in self.data
        ):
            del self.cleaned_data["include_apps"]
        return self.cleaned_data

    def is_valid(self, check_forms: typing.Dict[CheckId, "typing.Type[BaseCheckForm]"]) -> bool:  # type: ignore
        if not super().is_valid():
            return False
        checks = self.cleaned_data.get("checks", {})
        rforms = {
            name: check_forms[name](data=value)
            for name, value in checks.items()
            if name in check_forms
        }
        if forms.all_valid(rforms.values()):  # type: ignore
            self.cleaned_data["checks"] = {
                name: f.cleaned_data for name, f in rforms.items()
            }
            return True
        self.errors["checks"] = {name: form.errors for name, form in rforms.items()}
        return False


class BaseCheckForm(forms.Form):
    level = forms.ChoiceField(
        choices=[(c, c) for c in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]],
        required=False,
    )
    ignore_types = ListField(forms.CharField(), required=False)

    def clean_level(self) -> typing.Optional[int]:
        if self.cleaned_data["level"]:
            return getattr(django.core.checks, self.cleaned_data["level"])
        return None

    def clean_ignore_types(self) -> set:
        value = self.cleaned_data["ignore_types"]
        if not value:
            return value
        result = set()
        for import_path in value:
            try:
                path, entry = import_path.rsplit(".", 1)
                result.add(getattr(importlib.import_module(path), entry))
            except (ImportError, ValueError, AttributeError):
                raise forms.ValidationError(
                    f"ignore_types contains entry that can't be imported: '{import_path}'."
                )
        return result

    def clean(self) -> typing.Dict[str, typing.Any]:
        if (
            "ignore_types" in self.cleaned_data
            and not self.cleaned_data["ignore_types"]
        ):
            del self.cleaned_data["ignore_types"]
        return self.cleaned_data


class AttrsForm(BaseCheckForm):
    attrs = ListField(forms.CharField())
