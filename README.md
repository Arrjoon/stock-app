# NEPSE Stock App

Role-gated dashboard for NEPSE prices, floorsheet behavior, and tagged news.

## Run

```bash
cp .env.example .env
docker compose up --build
```

The web container migrates, loads `companies.yaml`, writes the Beat schedule, and queues the first news, price, and floorsheet fetch when those tables are empty. Later refreshes stay on the weekday schedule.

| What | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API health | http://localhost:8000/api/health/ |
| Swagger | http://localhost:8000/api/docs/ |
| Django admin | http://localhost:8000/admin/ |
| Flower | http://localhost:5555/ |

Sign in at `/login`. Create the accounts with:

```bash
docker compose exec web python manage.py seed_demo_users
```

| Email | Role | Password |
|---|---|---|
| admin@gmail.com | admin | admin |
| analyst@gmail.com | analyst | analyst |
| viewer@gmail.com | viewer | viewer |

If a host port is taken, change `FRONTEND_PORT`, `BACKEND_PORT`, `POSTGRES_PORT`, `REDIS_PORT`, and `NEXT_PUBLIC_API_URL` in `.env`, then rebuild the frontend. `NEXT_PUBLIC_*` is baked in at image build time.

Manual jobs, when you do not want to wait for Beat:

```bash
docker compose exec web python manage.py crawl_now --kind news --portal merolagani
docker compose exec web python manage.py crawl_now --kind prices
docker compose exec web python manage.py crawl_now --kind floorsheet
docker compose exec web python manage.py categorize_news
docker compose exec web python manage.py compute_analysis
docker compose exec web pytest
```

Without Docker, from `backend/`: install `requirements.txt`, `playwright install chromium`, `migrate`, `sync_beat_schedule`, `runserver`. Run the worker and Beat in other terminals:

```bash
celery -A config worker --loglevel=info -Q crawl,market,ml,celery -E
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Decisions

Crawls are Celery tasks on Redis, not one script. `crawl_now` and Beat only enqueue. One news task handles one portal. Beat has a separate row for MeroLagani, ShareSansar, and Bizmandu.

Every fetch checks robots.txt and then waits on a Redis lock (`SET NX PX`) so all workers share one gap per portal. A robots disallow is stored as a failed `CrawlRun` and is not bypassed. NepseAlpha stays off because its useful JSON is under `/api/*`, which robots.txt disallows.

httpx downloads list pages and article pages. BeautifulSoup parses HTML so tests can use saved fixtures. Playwright is only the MeroLagani **Load More** button. The setting is still named `use_selenium`. Article pages stay on httpx.

Prices and the floorsheet use `nepse-client` first. TLS verification is off only for that client (`NEPSE_TLS_VERIFY=false`) because the NEPSE certificate chain fails from Docker. The history payload has no open, so `open` is stored as `close`. The per-symbol floorsheet call returns 403, so the crawler samples the public floorsheet (up to 25 pages) and keeps active symbols. MeroLagani graph JSON and `Floorsheet.aspx` are the fallbacks.

Tags are keyword matches, not a trained model. A whole-word symbol is 0.95, the company name is 0.90, and an alias is 0.80. Manual tags are kept. An analyst correction is stored in `TagCorrection` and is not used to retrain anything yet.

Daily VWAP is `(high + low + close) / 3` because there are no intraday prints. Pressure is the close location inside the day's range, times volume. A volume z-score above 2.5 versus the previous 20 sessions is an anomaly.

Adding a company is a `companies.yaml` edit plus `sync_companies`. Crawlers only read `active=True`. Prices sit in the Timescale hypertable `market_price`. Django admin cannot register that composite primary key, so the admin uses a read-only view.

JSON responses are `{success, message, data}` or `{success: false, error: {code, message, details}}`. Role checks run on the server. The UI hides links. It does not grant access.

## Architecture

**accounts.** Custom user, role `admin` / `analyst` / `viewer`. JWT login and refresh. Admin user create and role change live at `/api/admin/users/`.

**companies.** Watchlist from `companies.yaml`. Read APIs for the company, prices (`7d`, `30d`, `90d`), behavior, behavior summary, and comparison ranks. Admin can patch name, aliases, and `active`. Analyst and admin can export CSV or JSON.

**market.** Daily OHLCV in `market_price`. Floorsheet rows are broker buy and sell prints. Price and floorsheet tasks run on the `market` queue.

**news.** One article row per normalized URL. Tags link an article to a company with confidence and source `auto` or `manual`. List pages collect URLs. Each new URL is its own `fetch_article` task on the `crawl` queue.

**analysis.** One result per company per price date: VWAP, pressure, volume anomaly, top brokers, news count, and the next session's return. Runs on the `ml` queue after the floorsheet, and again weekdays at 15:45 NPT.

**crawling.** `CrawlRun` records queued, running, success, and failed work. The base fetch applies robots, the rate limit, and httpx retries. Admin queues a run at `POST /api/admin/crawl-runs/`.

**realtime.** Daphne serves `/ws/updates?token=`. Events go out after the database commit. The dashboard refetches on a message, backs off if the socket drops, and polls every 30 seconds.

**frontend.** Next.js watchlist, company chart (close, VWAP, volume, anomaly), comparison ranks, and an admin desk for crawls and users. Viewers get a 403 page for admin actions.

**schedule.** News every `CRAWL_NEWS_MINUTES` (30). Prices Monday–Friday 15:00 NPT. Floorsheet 15:15 NPT. Behavior 15:45 NPT. Flower shows the worker on port 5555.

Portal selectors and field names are in [`docs/data-sources.md`](docs/data-sources.md).
