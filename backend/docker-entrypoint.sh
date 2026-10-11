#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  attempt=1
  until python manage.py migrate --noinput; do
    if [ "$attempt" -ge 10 ]; then
      echo "Database migrations failed." >&2
      exit 1
    fi
    attempt=$((attempt + 1))
    sleep 2
  done
  python manage.py sync_beat_schedule
  python manage.py sync_companies
  python manage.py bootstrap_sync
fi

exec "$@"
