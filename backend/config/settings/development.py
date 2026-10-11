"""
Development settings — extends base.py with dev-friendly overrides.
"""

from config.settings.base import *  # noqa: F403

DEBUG = env.bool("DEBUG", default=True)  # noqa: F405
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-change-me")  # noqa: F405
