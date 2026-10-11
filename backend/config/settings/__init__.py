"""
Settings package — auto-selects the right module based on DJANGO_ENV.

Usage:
    DJANGO_SETTINGS_MODULE=config.settings  (always this)
    DJANGO_ENV=development|production       (controls which sub-module loads)
"""

import os

env = os.environ.get("DJANGO_ENV", "development")

if env == "production":
    from config.settings.production import *  # noqa: F401, F403
else:
    from config.settings.development import *  # noqa: F401, F403
