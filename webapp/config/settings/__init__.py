"""
Environment-aware settings loader for SleepLens.
"""

from decouple import config

ENVIRONMENT = config("DJANGO_ENV", default="dev")

if ENVIRONMENT == "prod":
    from .prod import *
else:
    from .dev import *
