"""
Production settings — extends base.py with security hardening.
"""

import os

from django.core.exceptions import ImproperlyConfigured

from config.settings.base import *  # noqa: F403

DEBUG = env.bool("DEBUG", default=False)  # noqa: F405

# TLS terminates at the reverse proxy. Django only sees plain HTTP otherwise
# and builds http:// absolute URLs.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

_problems: list[str] = []

_secret = SECRET_KEY  # noqa: F405
if not _secret or _secret == "dev-only-change-me":
    _problems.append(
        "DJANGO_SECRET_KEY must be a real secret in production. "
        "The development placeholder is refused."
    )

if "ALLOWED_HOSTS" not in os.environ or not ALLOWED_HOSTS:  # noqa: F405
    _problems.append(
        "ALLOWED_HOSTS is required in production. Set it to the hosts that "
        "serve this API."
    )

if _problems:
    raise ImproperlyConfigured(
        "Refusing to start. "
        f"{len(_problems)} configuration problem(s):\n\n  - "
        + "\n  - ".join(_problems)
        + "\n"
    )
