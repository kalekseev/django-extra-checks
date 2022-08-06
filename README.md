# Django Extra Checks

Collection of useful checks for Django Checks Frameworks

## Checks

### Models

- **extra-checks-config** - settings.EXTRA_CHECKS is valid config for django-extra-checks (always enabled).
- **model-attribute** - Each Model in the project must have all attributes from `attrs` setting specified.
- **model-meta-attribute** - Each Model.Meta in the project must have all attributes from `attrs` setting specified.
- **no-unique-together** - Use UniqueConstraint with the constraints option instead.
- **no-index-together** - Use the indexes option instead.
- **model-admin** - Each model must be registered in admin.
- **field-file-upload-to** - FileField/ImageField must have non empty `upload_to` argument.
- **field-verbose-name** - All model's fields must have verbose name.
- **field-verbose-name-gettext** - verbose_name must use gettext.
- **field-verbose-name-gettext-case** - Words in text wrapped with gettext must be in one case.
- **field-help-text-gettext** - help_text must use gettext.
- **field-text-null** - text fields shouldn't use `null=True`.
- **field-boolean-null** - prefer using `BooleanField(null=True)` instead of `NullBooleanField`.
- **field-null** - don't pass `null=False` to model fields (this is django default).
- **field-foreign-key-db-index** - ForeignKey fields must specify `db_index` explicitly (to apply only to fields in indexes: `when: indexes`).
- **field-default-null** - If field nullable (`null=True`), then
  `default=None` argument is redundant and should be removed.
  **WARNING** Be aware that setting is database dependent,
  eg. Oracle interprets empty strings as nulls as a result
  django uses empty string instead of null as default.
- **field-choices-constraint** - Fields with choices must have companion CheckConstraint to enforce choices on database level, [details](https://adamj.eu/tech/2020/01/22/djangos-field-choices-dont-constrain-your-data/).

### DRF Serializers

- **drf-model-serializer-extra-kwargs** - ModelSerializer's extra_kwargs must not include fields that specified on serializer.
- **drf-model-serializer-meta-attribute** - Each ModelSerializer.Meta must have all attributes specified in `attrs`, [use case](https://hakibenita.com/django-rest-framework-slow#bonus-forcing-good-habits).

## Installation

Install with `pip install django-extra-checks`

Add `extra_checks` to `INSTALLED_APPS` (use `extra_checks.apps.ExtraChecksConfig` for Django versions prior to 3.2).

## Settings

To enable some check define `EXTRA_CHECKS` setting with a dict of checks and its settings:

```python
EXTRA_CHECKS = {
    "checks": [
        # require non empty `upload_to` argument.
        "field-file-upload-to",
        # use dict form if check need configuration
        # eg. all models must have fk to Site model
        {"id": "model-attribute", "attrs": ["site"]},
        # require `db_table` for all models, increase level to CRITICAL
        {"id": "model-meta-attribute", "attrs": ["db_table"], "level": "CRITICAL"},
    ]
}
```

By default only your project apps are checked but you can use
`include_apps` option to specify apps to check (including third party apps):

```python
EXTRA_CHECKS = {
    # use same names as in INSTALLED_APPS
    "include_apps": ["django.contrib.sites", "my_app"],
    ...
}
```

#### Ignoring check problems

Use `extra-checks-disable-next-line` comment to disable checks:

```python
# disable specific checks on model
# extra-checks-disable-next-line model-attribute, model-admin
class MyModel(models.Model):
    # disable all checks on image field
    # extra-checks-disable-next-line
    image = models.ImageField()

    # separate comments and check's codes are aslo supported
    # extra-checks-disable-next-line X014
    # extra-checks-disable-next-line no-unique-together
    class Meta:
        ...
```

Another way is to provide function that accepts field, model or
serializer class as its first argument and returns `True` if it must be skipped.
_Be aware that the more computation expensive your skipif functions the
slower django check will run._

`skipif` example:

```python
def skipif_streamfield(field, *args, **kwargs):
    return isinstance(field, wagtail.core.fields.StreamField)

def skipif_non_core_app(model_cls, *args, **kwargs):
    return model_cls._meta.app_label != "my_core_app"

EXTRA_CHECKS = {
    "check": [
        {
            "id": "field-verbose-name-gettext",
            # make this check skip wagtail's StreamField
            "skipif": skipif_streamfield
        },
        {
            "id": "model-admin",
            # models from non core app shouldn't be registered in admin
            "skipif": skipif_non_core_app,
        },
    ]
}
```

## Development

Install dev deps in virtualenv `pip install -e .[dev,test]`.

## Credits

The project was built using ideas and code snippets from:

- [Haki Benita](https://medium.com/@hakibenita/automating-the-boring-stuff-in-django-using-the-check-framework-3495fb550a6a)
- [Jon Dufresne](https://github.com/jdufresne/django-check-admin)
- [Adam Johnson](https://adamj.eu/tech/2020/01/22/djangos-field-choices-dont-constrain-your-data/)
