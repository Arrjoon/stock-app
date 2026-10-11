# Data sources (Section 1 discovery)

Verified portal behavior for news and NEPSE market crawls. Do not re-discover;
implement against these notes.

## Robots.txt (verified)

| Portal | robots.txt URL | Status | Disallowed paths | Crawl-Delay |
|---|---|---|---|---|
| MeroLagani | `https://merolagani.com/robots.txt` | 404 Not Found | None | None |
| ShareSansar | `https://www.sharesansar.com/robots.txt` | 200 OK | `User-agent: *` / `Disallow:` (all allowed) | None |
| NepseAlpha | `https://nepsealpha.com/robots.txt` | 200 OK | `/admin/*`, `/api/*`, `/trading/1/*`, `/trading/0/*`, `/force-url-key`, `/trading-menu/*`, `/rest/v1/*` | None |
| Bizmandu | `https://www.bizmandu.com/robots.txt` | 200 OK | Content signals block restricting AI training; no path disallows | None |

**Decision:** Exclude NepseAlpha from automated crawling. `/api/*` is disallowed
and the official API is paid. `enabled: False` in settings. No crawler class.

Crawlers check robots.txt with `urllib.robotparser` before every request and
never bypass a disallow.

## MeroLagani — news

| Item | Value |
|---|---|
| List URL | `https://merolagani.com/NewsList.aspx` |
| Pagination | ASP.NET page with a **Load More** control (`a[data-load="news-block-three"]`, `data-page`, `data-page-size="8"`). First page is available over HTTP. Extra pages need a rendered browser (Playwright) to click Load More. |
| Article URL | `https://merolagani.com/NewsDetail.aspx?newsID={id}` |
| Headline | `<meta property="og:title">` or `h4.newsTitle` |
| Body | `#ctl00_ContentPlaceHolder1_newsOverview` / `div.media-content` |
| Date | `#ctl00_ContentPlaceHolder1_newsDate` / `span.media-label` e.g. `Oct 11, 2026 11:22 AM` |
| Date format | Mixed Nepali (BS) and Gregorian. Store raw in `Article.raw_date`. Parse when possible; leave `published_at` null on failure and log a warning. |
| JSON endpoint | `https://merolagani.com/handlers/webrequesthandler.ashx?type=get_company_graph&symbol={SYM}&dateRange=12` returns `quotes[]` with `date`, `open`, `close`, `high`, `low`, `volumen` (misspelled), `rsi`. Used as market-data fallback. |

**Rate limit:** `min_interval = 2.0` seconds.

**List cards:** `div.news-list a[href*="NewsDetail.aspx"]`. First HTTP GET already
contains article links; Playwright is only required to walk further pages.

## MeroLagani — floorsheet (fallback)

| Item | Value |
|---|---|
| URL | `https://merolagani.com/Floorsheet.aspx` |
| Columns | `#`, `Transact. No.`, `Symbol`, `Buyer`, `Seller`, `Quantity`, `Rate`, `Amount` |
| Records per page | 500 |
| Pagination | Total pages shown (e.g. 105 pages / 52,044 records). Date filter available. |
| Broker links | `/BrokerDetail.aspx?code={code}` |
| Symbol links | `/CompanyDetail.aspx?symbol={symbol}` |

Primary floorsheet source is `nepse-client` `getFloorSheet()`. The per-symbol
`getFloorSheetOf` endpoint currently returns HTTP 403, so the crawler samples
the latest session (up to 25 pages) and keeps rows for active companies.
`Floorsheet.aspx` is the fallback when that sample is empty.

## ShareSansar — news

| Item | Value |
|---|---|
| List URL | `https://www.sharesansar.com/category/latest-news` (variants: `exclusive`, `ipo-fpo-news`, `proposed-dividend`) |
| Pagination | Cursor-style (`next_cursor` → `cursor`) when the markup exposes it; otherwise `?page=N`. First page already lists many `/newsdetail/{slug}` links. |
| Article URL | `https://www.sharesansar.com/newsdetail/{slug}-{date}` |
| Headline | `<meta property="og:title">` or `div.detail h1` |
| Body | `#newsdetail-content` |
| Date | Prefer the `YYYY-MM-DD` suffix in the slug or visible `i.date` (`11 Oct, 2026`). Site-wide `<meta property="article:published_time">` is often a stale 2016 value — do not trust it when it disagrees with the slug. |
| Date format | Gregorian. Slug date and visible date parse directly. |
| RSS | None found. |

**Rate limit:** `min_interval = 1.5` seconds.

## NepseAlpha — news (excluded)

| Item | Value |
|---|---|
| List URL | `https://nepsealpha.com/` (articles under `/post/detail/{id}`) |
| JSON endpoint | `POST https://nepsealpha.com/api/smx9841/dashboard_board` — **violates robots.txt**. |
| Decision | **Exclude entirely.** `enabled: False`. Do not write a crawler. |

## Bizmandu — news

| Item | Value |
|---|---|
| List URL | `https://wp.bizmandu.com/content/category/market.html` (NOT `bizmandu.com/market` — that 404s) |
| Pagination | `/page/{n}` — e.g. `.../market.html/page/2` |
| Article URL | `https://wp.bizmandu.com/content/{id}.html` (numeric or timestamp ids) |
| Headline | `<meta property="og:title">` or `h1.detail_title` |
| Body | `div.news-text` inside `div.biz-article-content` |
| Date | Calendar span near the title, e.g. `२०७९ मंसिर २८ गते … \| Dec 14, 2022`. Also `article:published_time` when present. |
| Date format | Mixed Nepali (BS) and Gregorian. Same handling as MeroLagani. |
| RSS | None found. |

**Rate limit:** `min_interval = 2.0` seconds.

## NEPSE trading data

Use **`nepse-client`** (PyPI). Verified methods:

| Method | Purpose |
|---|---|
| `client.getCompanyPriceVolumeHistory(symbol, start_date, end_date)` | OHLCV history |
| `client.getFloorSheet()` | Full session floorsheet |
| `client.getFloorSheetOf(symbol, business_date)` | Filtered floorsheet |

**TLS workaround:** `client.setTLSVerification(False)` — scoped to this client
only. Documented in the README.

**Fallback:** MeroLagani `get_company_graph` for prices and `Floorsheet.aspx`
for a sample of trades when `nepse-client` fails.

**Fallback libraries (untested):** `NepseUnofficialApi`, `nepseman-api`,
`nepse-data-api`.

## NEPSE trading hours

| Item | Value |
|---|---|
| Trading days | Monday to Friday (effective April 6, 2026) |
| Market open | 11:00 AM NPT |
| Market close | 3:00 PM NPT |
| Time zone | Asia/Kathmandu |

Beat runs prices at 15:00 NPT and floorsheet shortly after, Mon–Fri.

## Watchlist

Crawlers loop `Company.objects.filter(active=True)`. Adding a company is
`companies.yaml` + `python manage.py sync_companies`.

## Settings shape

Portal URLs, `min_interval`, `max_pages`, and `enabled` live in
`CRAWLER_CONFIG` (django-environ overrides). NepseAlpha stays `enabled: False`.
