SECRET_KEY = "random"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.sites",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "tests.example",
    "extra_checks",
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}

EXTRA_CHECKS = {
    "include_apps": ["tests.example"],
    "checks": [
        # require non empty `upload_to` argument.
        "field-file-upload-to",
        # use dict form if check need configuration
        # eg. all models must have fk to Site model
        {"id": "model-attribute", "attrs": ["site"]},
        # require `db_table` for all models, increase level to CRITICAL
        {"id": "model-meta-attribute", "attrs": ["db_table"], "level": "CRITICAL"},
    ],
}
ROOT_URLCONF = "tests.urls"

SILENCED_SYSTEM_CHECKS = [
    "fields.E210",
]
