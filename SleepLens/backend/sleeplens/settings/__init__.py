"""Environment-based settings loader.

DJANGO_ENV selects the settings module: dev (default), test, prod.
"""

from __future__ import annotations

import os

_env = os.getenv("DJANGO_ENV", "dev")

if _env == "prod":
    from .prod import *  # noqa: F403
elif _env == "test":
    from .test import *  # noqa: F403
else:
    from .dev import *  # noqa: F403
