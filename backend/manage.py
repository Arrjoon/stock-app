#!/usr/bin/env python
"""Django entrypoint for the NEPSE stock app."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Install backend dependencies first."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
