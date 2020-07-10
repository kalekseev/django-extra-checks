# Django Extra Checks

Useful checks for Django Checks Frameworks

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

To ignore all warnings on some object you can use `ignore_checks` decorator:

```python
from extra_checks import ignore_checks, CheckID

@ignore_checks("model-attribute", "X011", CheckID.X050)
class MyModel(models.Model):
    image = models.ImageField()
```

Another way is to specify type of the object that need to be ignored in `ignore_types` option:

```python
EXTRA_CHECKS = {
    "check": [
        {
            "id": "field-verbose-name-gettext",
            # make this check skip wagtail's StreamField
            "ignore_types": ["wagtail.core.fields.StreamField"],
        }
    ]
}
```

## Checks

### Models

- **extra-checks-config** - settings.EXTRA_CHECKS is valid config for django-extra-checks (always enabled).
- **model-attribute** - Each Model in the project must have all attributes from `attrs` setting specified.
- **model-meta-attribute** - Each Model.Meta in the project must have all attributes from `attrs` setting specified.
- **model-admin** - Each model must be registered in admin.
- **field-file-upload-to** - FileField/ImageField must have non empty `upload_to` argument.
- **field-verbose-name** - All model's fields must have verbose name.
- **field-verbose-name-gettext** - verbose_name must use gettext.
- **field-verbose-name-gettext-case** - Words in text wrapped with gettext must be in one case.
- **field-help-text-gettext** - help_text must use gettext.
- **field-text-null** - text fields shoudn't use `null=True`.
- **field-boolean-null** - prefer using `BooleanField(null=True)` instead of `NullBooleanField`.
- **field-null** - don't pass `null=False` to model fields (this is django default).
- **field-foreign-key-index** - ForeignKey fields must specify `db_index` explicitly (to apply to unique together only: `when: unique_together`).
- **field-default-null** - If field nullable (`null=True`), then
    `default=None` argument is redundant and should be removed.
    **WARNING** Be aware that setting is database dependent,
    eg. Oracle interprets empty strings as nulls as a result
    django uses empty string instead of null as default.

### DRF Serializers

- **drf-model-serializer-extra-kwargs** - ModelSerializer's extra_kwargs must not include fields that specified on serializer.
- **drf-model-serializer-meta-attribute** - Each ModelSerializer.Meta must have all attributes specified in `attrs`, [use case](https://hakibenita.com/django-rest-framework-slow#bonus-forcing-good-habits).

## Development

Install dev deps in virtualenv `pip install -e .[dev]`.

## Credits

The project was built using ideas and code snippets from:

- [Haki Benita](https://medium.com/@hakibenita/automating-the-boring-stuff-in-django-using-the-check-framework-3495fb550a6a)
- [Jon Dufresne](https://github.com/jdufresne/django-check-admin)
