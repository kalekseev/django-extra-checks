from extra_checks import CheckId

SECRET_KEY = "random"

ALLOWED_HOSTS = ["*"]
USE_TZ = True

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

EXTRA_CHECKS = {
    "include_apps": ["tests.example"],
    "level": "ERROR",
    "checks": [
        # require non empty `upload_to` argument.
        "field-file-upload-to",
        # use dict form if check need configuration
        # eg. all models must have fk to Site model
        {"id": "model-attribute", "attrs": ["site"]},
        # require `db_table` for all models, increase level to ERROR
        {"id": "model-meta-attribute", "attrs": ["db_table"], "level": "ERROR"},
        {"id": "drf-model-serializer-meta-attribute", "attrs": ["read_only_fields"]},
    ],
}

_checks = [c["id"] if isinstance(c, dict) else c for c in EXTRA_CHECKS["checks"]]
EXTRA_CHECKS["checks"].extend(list(CheckId._value2member_map_.keys() - _checks))  # type: ignore

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

MIDDLEWARE = [
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
]

ROOT_URLCONF = "tests.urls"

SILENCED_SYSTEM_CHECKS = ["fields.E210"]
