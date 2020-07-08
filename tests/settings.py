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
