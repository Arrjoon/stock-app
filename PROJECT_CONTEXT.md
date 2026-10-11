# NEPSE Stock Market App

Crawl news from merolagani, sharesansar, nepsealpha, bizmandu and 1 month of
NEPSE trading data (OHLCV + floorsheet) for 5-10 companies. Auto-tag news by
company with confidence, analyze buyer/seller behavior, and serve everything
through a role-gated dashboard with live updates.

## Stack

- Backend: Django 5 + Django REST Framework
- Auth: djangorestframework-simplejwt, custom User with role field
- DB: Postgres + TimescaleDB
- Queue/scheduler: Celery + Redis + django-celery-beat
- Realtime: Django Channels + channels-redis (Daphne), WS at /ws/updates
- API docs: drf-spectacular
- Config: django-environ
- Frontend: Next.js (App Router) + Tailwind
- Infra: docker-compose

## Roles

- Admin: manage watchlist, trigger/monitor crawls, manage users
- Analyst: view all, correct categorization, export reports
- Viewer: read-only

## API (planned)

- GET /api/companies
- GET /api/companies/{id}/prices?range=30d
- GET /api/news?company_id=
- POST /api/news/{id}/recategorize
- GET /api/companies/{id}/behaviorsummary
- GET /api/compare
- POST|GET /api/admin/crawl-runs
- GET /api/admin/users
- POST /api/auth/login, /api/auth/refresh
- WS /ws/updates
