from .check_id import CheckId
from .registry import ignore_checks

default_app_config = "extra_checks.apps.ExtraChecksConfig"


__all__ = [
    "ignore_checks",
    "CheckId",
]
