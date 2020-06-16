SECRET_KEY = "random"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = ["django.contrib.sites", "tests.example"]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}

ROOT_URLCONF = "tests.urls"
