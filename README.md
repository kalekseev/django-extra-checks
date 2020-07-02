# Django Extra Checks

Useful checks for Django Checks Frameworks

## Settings

To enable some check define `EXTRA_CHECKS` setting with a dict of
checks and its settings, eg:

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

To ignore model warnings you can use `ignore_checks` decorator, eg:

```python
from extra_checks import ignore_checks, CheckID

@ignore_checks("model-attribute", "X011", CheckID.X050)
class MyModel(models.Model):
    image = models.ImageField()
```

## Checks

- **extra-checks-config** - settings.EXTRA_CHECKS is valid config for django-extra-checks (always enabled).
- **model-attribute** - Each Model in the project must have all attributes from `attrs` setting specified.
- **model-meta-attribute** - Each Model.Meta in the project must have all attributes from `attrs` setting specified.
- **field-file-upload-to** - FileField/ImageField must have non empty `upload_to` argument.
- **field-verbose-name** - All model's fields must have verbose name.
- **field-verbose-name-gettext** - verbose_name must use gettext.
- **field-verbose-name-gettext-case** - Words in text wrapped with gettext must be in one case.
- **field-help-text-gettext** - help_text must use gettext.
- **field-text-null** - text fields shoudn't use `null=True`.
- **field-boolean-null** - prefer using `BooleanField(null=True)` instead of `NullBooleanField`.
- **field-null-false** - don't pass `null=False` to model fields (this is django default).
- **field-foreign-key-index** - ForeignKey fields must specify `db_index` explicitly.

## Development

Install dev deps in virtualenv `pip install -e .[dev]`.

## Credits

The project was built using ideas and code snippets from:

- [Haki Benita](https://medium.com/@hakibenita/automating-the-boring-stuff-in-django-using-the-check-framework-3495fb550a6a)
