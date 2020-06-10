# Django Extra Checks

Useful checks for Django Checks Frameworks

## Settings

To enable some check define `EXTRA_CHECKS` setting with a dict of
checks and its settings, eg:

```python
EXTRA_CHECKS = {
    "checks": [
        # require non empty `upload_to` argument.
        'X002',
        # use dict form if check need configuration
        # eg. all models must have fk to Site model
        {"id": "X003", "attrs": ["site"]},
        # require `db_table` for all models, increase level to CRITICAL
        {"id": "X004", "attrs": ["db_table"], "level": "CRITICAL"},
    ]
}
```

To ignore model warnings you can use `ignore_checks` decorator, eg:

```python
from extra_checks import ignore_checks, CheckID

@ignore_checks("X002", CheckID.X003)
class MyModel(models.Model):
    image = models.ImageField()
```

## Checks

- **X001** - settings.EXTRA_CHECKS is valid config for django-extra-checks (always enabled).
- **X002** - FileField/ImageField must have non empty `upload_to` argument.
- **X003** - Each Model in the project must have all attributes from `attrs` setting specified.
- **X004** - Each Model.Meta in the project must have all attributes from `attrs` setting specified.
- **X005** - All model's fields must have verbose name.
- **X006** - verbose_name must use gettext
- **X007** - Words in text wrapped with gettext must be in one case.
- **X008** - help_text must use gettext

## Development

Install dev deps in virtualenv `pip install -e .[dev]`.

## Credits

The project was built using ideas and code snippets from:

- [Haki Benita](https://medium.com/@hakibenita/automating-the-boring-stuff-in-django-using-the-check-framework-3495fb550a6a)
