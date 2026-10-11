# Project: NEPSE Stock Market App (Omway Technologies assignment)

## Goal
Crawl news from merolagani, sharesansar, nepsealpha, bizmandu and 1 month of
NEPSE trading data (OHLCV + floorsheet) for 5-10 companies. Auto-tag news by
company with confidence, analyze buyer/seller behavior, and serve everything
through a role-gated dashboard with live updates.

## Stack (fixed, do not substitute)
- Backend: Django 5 + Django REST Framework (NO FastAPI)
- Auth: djangorestframework-simplejwt, custom User with role field
- DB: Postgres + TimescaleDB (Price table is a hypertable)
- Queue/scheduler: Celery + Redis + django-celery-beat
- Realtime: Django Channels + channels-redis (Daphne), WS at /ws/updates
- API docs: drf-spectacular (Swagger)
- Config: django-environ, no hard-coded secrets
- Frontend: Next.js (App Router) + Tailwind + Recharts, responsive desktop/tablet
- Infra: docker-compose for the full stack

## Target structure
stock-app/
├── docker-compose.yml
├── .env.example
├── companies.yaml            # adding a company = config change only
├── README.md  FINDINGS.md  PROJECT_CONTEXT.md
├── backend/
│   ├── manage.py, requirements.txt, Dockerfile
│   ├── config/               # settings, urls, asgi, celery
│   └── apps/
│       ├── accounts/         # User(role), JWT, permissions
│       ├── companies/        # Company + sync_companies command
│       ├── market/           # Price, Floorsheet, crawlers
│       ├── news/             # Article, ArticleTag, TagCorrection, crawlers, categorizer
│       ├── analysis/         # vwap, pressure, anomaly, brokers
│       ├── crawling/         # CrawlRun, base crawler, rate limiter
│       └── realtime/         # Channels consumer, notify helper
└── frontend/                 # Next.js: login, company, compare, admin pages

## Roles
- Admin: manage watchlist, trigger/monitor crawls, manage users
- Analyst: view all, correct categorization, export reports
- Viewer: read-only
Every role check is enforced server-side with DRF permission classes.

## API (extend as needed)
GET /api/companies | GET /api/companies/{id}/prices?range=30d
GET /api/news?company_id= | POST /api/news/{id}/recategorize (analyst/admin)
GET /api/companies/{id}/behaviorsummary | GET /api/compare
POST|GET /api/admin/crawl-runs (admin) | /api/admin/users (admin)
POST /api/auth/login, /api/auth/refresh | WS /ws/updates

## Analysis definitions
- VWAP = sum(typical_price * volume)/sum(volume), typical = (H+L+C)/3
- Pressure = close location value ((C-L)-(H-C))/(H-L) * volume, 5-day rolling
- Volume anomaly = 20-day rolling z-score > 2.5
- Broker net buy/sell from floorsheet
- News count vs next-day return/volume correlation

## Rules for Cursor
- Work one phase at a time; verify before moving on; small commits.
- Central exception handler, uniform error JSON, serializers validate input.
- Failures from crawls/API must be stored (CrawlRun) and shown in Admin view.
- Prefer simple, readable code over cleverness (time-boxed assignment).
- Never leave unused code, dead files or leftover boilerplate.