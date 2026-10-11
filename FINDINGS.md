# Findings

Short notes from running the crawlers and the dashboard. Selectors live in [`docs/data-sources.md`](docs/data-sources.md).

## News sites

- **NepseAlpha is not crawled.** `robots.txt` disallows `/api/*`, and that is where the useful JSON sits.
- **MeroLagani page 1 is plain HTML.** Later pages are an ASP.NET Load More button, so only that step uses Playwright. Article pages stay on httpx.
- **ShareSansar `article:published_time` is often stuck in 2016.** The date in the URL slug is the one to keep.
- **`bizmandu.com/market` returns 404.** The list that works is `https://wp.bizmandu.com/content/category/market.html`.
- **MeroLagani and Bizmandu dates mix Nepali BS and Gregorian.** The raw string is stored. `published_at` is set only when the Gregorian part parses.

## Prices and floorsheet

- **`nepse-client` is the primary source.** TLS checks are off only for that client. The NEPSE certificate fails from Docker.
- **History has no open.** `open` is stored as `close`.
- **`getFloorSheetOf` returns 403.** The crawler samples the public floorsheet, up to 25 pages, and keeps active symbols. MeroLagani `Floorsheet.aspx` is the fallback.
- **Prices are a Timescale hypertable** (`market_price`) on `(company, date)`. Django admin cannot register that key, so Prices in admin is a read-only view.

## Tagging

- **Tags are keyword matches**, not a model. Symbol 0.95, full name 0.90, alias 0.80. A symbol inside another word does not match.
- **`categorize_news` is not a background job.** New articles are tagged by the Celery task `categorize_article` on the `ml` queue. The command only retags what is already in the database.
- **Articles saved before the watchlist existed were marked categorized with zero tags** and then skipped. `categorize_news` now retries articles that have no tags.
- **“Most in the news” counts tags from the last 30 days.** After retagging, NICA led that window (6), then SCB (3).

## Behavior

- **Daily VWAP is `(high + low + close) / 3`.** There are no intraday prints to weight by volume.
- **A volume anomaly is a 20-day z-score above 2.5.**
- **Broker rank is net quantity** from the floorsheet: buy quantity minus sell quantity.
