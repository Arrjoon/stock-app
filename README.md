# NEPSE Stock App

Role-gated dashboard for NEPSE prices, floorsheet behavior, and tagged news.
Crawling, automatic company tagging, buyer/seller behavior, the DRF API, and
the live Next.js dashboard are implemented.

Discovery notes live in [`docs/data-sources.md`](docs/data-sources.md).

## Stack

Django 5 + DRF, Next.js, TimescaleDB, Redis, Celery, Channels (Daphne),
httpx, BeautifulSoup, Playwright (MeroLagani list pagination only),
`nepse-client`.

## Setup

```bash
cp .env.example .env
docker compose up --build
```

- UI: http://localhost:3000
- API health: http://localhost:8000/api/health/
- Swagger: http://localhost:8000/api/docs/
- Django admin: http://localhost:8000/admin/
- Flower (Celery tasks): http://localhost:5555/
- JWT: `POST /api/auth/login`, `POST /api/auth/refresh`

If 3000, 8000, 5432, or 6379 are already in use, change `FRONTEND_PORT`,
`BACKEND_PORT`, `POSTGRES_PORT`, `REDIS_PORT`, and `NEXT_PUBLIC_API_URL` in `.env`.

Watchlist symbols live in `companies.yaml`. Adding a company is a config change.

```bash
docker compose exec web python manage.py sync_companies
docker compose exec web python manage.py seed_demo_users
docker compose exec web python manage.py crawl_now --kind news --portal merolagani
docker compose exec web python manage.py crawl_now --kind prices
docker compose exec web python manage.py crawl_now --kind floorsheet
docker compose exec web python manage.py categorize_news
docker compose exec web python manage.py compute_analysis
```

`sync_companies` upserts rows from `companies.yaml`. Crawlers always loop
`Company.objects.filter(active=True)`.

Demo user passwords come from `SEED_*_PASSWORD` in `.env`.

## API and live dashboard

OpenAPI is at http://localhost:8000/api/docs/ (`/api/schema/`). Every JSON
response uses `{success, message, data}` or `{success: false, error: {code, message, details}}`.

Viewer and above:

- `GET /api/companies/`
- `GET /api/companies/{symbol-or-id}/`
- `GET /api/companies/{symbol-or-id}/prices/?range=7d|30d|90d`
- `GET /api/companies/{symbol-or-id}/behavior/?range=7d|30d|90d`
- `GET /api/news/?company_id=`
- `GET /api/compare/?range=30d` — most volatile (stdev of daily returns), most active (sum of volume), most in the news (tagged articles)

Analyst and admin: `POST /api/news/{id}/recategorize/` with `{"company_ids": [1]}`.

An admin can press **Sync now** in the header. That queues news, prices, and the floorsheet immediately. On a fresh database the web container queues the same jobs at startup, then Beat keeps the weekday schedule.

The dashboard signs in at `/login`, stores the JWT, and opens
`ws://<api-host>/ws/updates?token=...`. New articles, recategorization,
price crawls, and behavior runs publish on that socket so the company page
and the comparison page refetch. Prices live in the Timescale hypertable
`market_price`. Crawl and inference jobs stay on Redis/Celery.

If live NEPSE history is unreachable:

```bash
docker compose exec web python manage.py load_seed_prices
```

## How scraping works

Jobs are **not** a single script. `crawl_now` and Celery Beat enqueue tasks on
Redis. A worker consumes three queues:

| Queue | Tasks |
|---|---|
| `crawl` | `crawl_portal_news`, `fetch_article` |
| `market` | `crawl_prices`, `crawl_floorsheet` |
| `ml` | `categorize_article`, `compute_behavior` |

`crawl_portal_news` only collects URLs, skips rows already in `Article`, and
fans out one `fetch_article` task per new URL. It does not download every
article inline.

Every HTTP request:

1. Normalizes the URL (no fragment, no `utm_*`, no trailing slash).
2. Checks robots.txt via `urllib.robotparser`. A disallow raises
   `RobotsDisallowedError` and is never bypassed.
3. Takes a Redis `SET NX PX` slot so all workers share one `min_interval`
   per portal.
4. Fetches with **httpx** (timeouts, redirects, retries via **tenacity** on
   network errors, 429, and 5xx).

Failures are written to `CrawlRun` (`status=failed`, `error=...`) and to
`backend/logs/crawler.log` (rotating file) plus the console.

### Why these tools

| Tool | Why |
|---|---|
| **httpx** | Shared HTTP client for list pages, article pages, and JSON. Follows redirects, has timeouts, works inside Celery workers. |
| **BeautifulSoup + lxml** | Parsers are pure functions of HTML so pytest can run against saved fixtures with no network. |
| **Playwright (Chromium)** | MeroLagani news listing is ASP.NET. Page 1 is normal HTML, but extra pages are a **Load More** button (`data-load="news-block-three"`) that needs a real browser click. Playwright is used only for that listing. Article pages are httpx. |
| **urllib.robotparser** | Standard robots.txt check. NepseAlpha `/api/*` is disallowed, so that portal is disabled and has no crawler. |
| **Redis SET NX PX** | Rate limit is global across worker processes, not just in-process sleep. |
| **Celery + Beat + Redis** | News every 30 minutes; prices at 15:00 NPT Mon–Fri; floorsheet at 15:15 NPT Mon–Fri. Schedules are `PeriodicTask` rows (`sync_beat_schedule`). |
| **nepse-client** | Official-style NEPSE REST wrapper for OHLCV and floorsheet. TLS verification is turned off **only** on this client (`NEPSE_TLS_VERIFY=false`) because the NEPSE certificate chain often fails from Docker. |
| **MeroLagani JSON / Floorsheet.aspx** | Fallback if `nepse-client` errors or returns nothing. |

NepseAlpha is **not crawled**. Its useful JSON lives under `/api/*`, which
robots.txt disallows.

### MeroLagani (`merolagani.com`) — 2.0s gap

1. `GET https://merolagani.com/NewsList.aspx` with httpx.
2. Parser collects `a[href*="NewsDetail.aspx?newsID="]`.
3. If `use_selenium=true` and `max_pages>1`, Playwright opens the same URL and
   clicks **Load More** up to `max_pages` snapshots.
4. New URLs become `fetch_article` tasks.
5. Each article: `GET NewsDetail.aspx?newsID=…`
   - title: `og:title` or `h4.newsTitle`
   - body: `#ctl00_ContentPlaceHolder1_newsOverview`
   - date: `#ctl00_ContentPlaceHolder1_newsDate` (`Oct 11, 2026 11:21 AM`)
6. Gregorian dates become `published_at`. Nepali-only dates stay in `raw_date`.

Price fallback:
`GET …/handlers/webrequesthandler.ashx?type=get_company_graph&symbol=NABIL&dateRange=12`
(`quotes[].volumen` is the volume field).

Floorsheet fallback: parse `Floorsheet.aspx` table columns Transact. No.,
Symbol, Buyer, Seller, Quantity, Rate, Amount; keep active symbols only.

### ShareSansar (`www.sharesansar.com`) — 1.5s gap

1. `GET /category/latest-news`.
2. Collect `/newsdetail/{slug}` links. Extra pages use `?cursor=` when
   `next_cursor` is present, otherwise `?page=N`.
3. Article parse:
   - title: `og:title` or `div.detail h1`
   - body: `#newsdetail-content`
   - date: slug `YYYY-MM-DD` or `i.date`. The site-wide
     `article:published_time` is often a stale 2016 value and is ignored when
     the slug date is newer.

No Selenium. First page is enough HTML for httpx.

### Bizmandu (`wp.bizmandu.com`) — 2.0s gap

`bizmandu.com/market` 404s. The working list is
`https://wp.bizmandu.com/content/category/market.html`.

1. Page 1 is that URL; later pages are `{list}/page/{n}`.
2. Article links match `/content/{id}.html` (skip category/feed/ads).
3. Article parse:
   - title: `og:title` or `h1.detail_title`
   - body: `div.biz-article-content div.news-text`
   - date: calendar span (`२०७९ … | Dec 14, 2022`) plus `article:published_time`

No Selenium.

### NEPSE prices and floorsheet

Primary source: `nepse-client`

- `getCompanyPriceVolumeHistory(symbol, start, end)` — about a month of daily
  bars. The payload has high, low, close, volume, turnover, and trades. It
  does not include open, so `open` is stored as `close`.
- `getFloorSheetOf(symbol, business_date)` is the per-company endpoint. It
  currently returns HTTP 403. The crawler then samples the latest session from
  `getFloorSheet(page=…)` (up to 25 pages) and keeps rows for active symbols.

Rows upsert into Timescale hypertable `market_price` (unique company+date).
Floorsheet uses `bulk_create(..., ignore_conflicts=True)`.

Per-company failures are appended to `CrawlRun.error` and do not abort the
whole run.

## Celery

```bash
docker compose exec worker celery -A config inspect active
docker compose exec web python manage.py sync_beat_schedule
```

Flower is http://localhost:5555/ (`FLOWER_PORT`). It reads worker events from the same Redis broker, so the worker is started with `-E`. Set `FLOWER_BASIC_AUTH=user:password` to require a login.

Beat uses `DatabaseScheduler`. News portals every `CRAWL_NEWS_MINUTES`
(default 30). Prices after close Mon–Fri 15:00 NPT; floorsheet 15:15 NPT;
behavior recompute at 15:45 NPT. A floorsheet crawl also queues
`compute_behavior` when it finishes.

## Automatic categorization

After each new article is saved, `categorize_article` runs on the `ml` queue.
It checks the title and body against every active company:

| Match | Confidence |
|---|---|
| Symbol as a whole word (`NABIL`) | 0.95 |
| Full company name | 0.90 |
| Alias (`Nabil Bank`, `Nepal Telecom`) | 0.80 |

A hit is stored as `ArticleTag` with `source=auto` and `matched_on` listing the terms. The same URL is not tagged twice. Manual tags are not replaced. Words that only contain the symbol (`SCNABILX`) are ignored. `categorize_news` retags articles already in the database.

## Buyer and seller behavior

`compute_analysis` writes one `AnalysisResult` per company per price date:

- **VWAP** for a daily bar is `(high + low + close) / 3`. `close_vs_vwap_pct` is how far the close sits from that.
- **Pressure** is `((close - low) - (high - close)) / (high - low) * volume`. `pressure_5d` is the 5-day average.
- **Volume anomaly** is a z-score of today's volume against up to 20 earlier sessions. Above 2.5 is flagged.
- **Brokers** are ranked from the floorsheet. Each broker's `net_qty` is buy quantity minus sell quantity. `top_buyers` are the largest net buyers. `top_sellers` are the largest net sellers. Each row includes buy quantity, sell quantity, and amounts.
- **News count** is how many tagged articles were published that day. Next-day return and volume change use the following trading session.

Weekdays at 15:45 NPT, Beat runs the same job again.

## Tests

```bash
docker compose exec web pytest
```

Parser, robots, rate-limit, upsert, and Celery tests use fixtures under
`backend/tests/fixtures/` and do not hit the network.

## Local development without Docker

```bash
cp .env.example .env
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python manage.py migrate
python manage.py sync_beat_schedule
python manage.py runserver
```

Celery (separate terminals):

```bash
celery -A config worker --loglevel=info -Q crawl,market,ml,celery -E
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
celery -A config flower --port=5555
```

## Environment

Copy `.env.example`. Do not commit real secrets. Compose overrides
`DATABASE_URL` and Redis URLs inside the containers.

Portal URLs, `min_interval`, `max_pages`, and `enabled` are env-overridable
(`CRAWLER_MEROLAGANI_*`, `CRAWLER_SHARESANSAR_*`, `CRAWLER_BIZMANDU_*`,
`CRAWLER_NEPSEALPHA_ENABLED=false`).
