# NEPSE Stock App

Role-gated dashboard for NEPSE prices, floorsheet behavior, and tagged news.
This commit is the project skeleton only — crawlers and analysis are not implemented yet.

## Stack

Django 5 + DRF, Next.js, TimescaleDB, Redis, Celery, Channels (Daphne).

## Setup

```bash
cp .env.example .env
docker compose up --build
```

- UI: http://localhost:3000
- API health: http://localhost:8000/api/health/
- Swagger: http://localhost:8000/api/docs/
- JWT: `POST /api/auth/login`, `POST /api/auth/refresh`

If 3000, 8000, 5432, or 6379 are already in use, change `FRONTEND_PORT`, `BACKEND_PORT`, `POSTGRES_PORT`, `REDIS_PORT`, and `NEXT_PUBLIC_API_URL` in `.env`.

Placeholder pages: `/login`, `/companies/[id]`, `/compare`, `/admin`.

Watchlist symbols live in `companies.yaml`. Adding a company is a config change.

```bash
docker compose exec web python manage.py sync_companies
docker compose exec web python manage.py seed_demo_users
```

`sync_companies` upserts rows from `companies.yaml`. Demo user passwords come from `SEED_*_PASSWORD` in `.env`.

## Local development without Docker

Backend:

```bash
cp .env.example .env
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Celery (separate terminals):

```bash
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment

Copy `.env.example`. Do not commit real secrets. Compose overrides `DATABASE_URL` and Redis URLs inside the containers so they talk to the `db` and `redis` services.
