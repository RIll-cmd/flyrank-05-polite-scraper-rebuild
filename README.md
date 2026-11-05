# The polite scraper

Rebuilt on 2026-11-05 from the prior assignment implementation, incrementally with fresh checkpoint evidence. This is AI-assisted work, not a claim of original hand-written work or historical stage dates.

Target: https://books.toscrape.com/; scope: catalogue pages 1–3 and their 60 linked public products. ToScrape explicitly presents this as a scraping practice sandbox. robots.txt returned 404; absence alone is not permission.

I will not reuse this code on another site without checking its rules and terms first.

## Run in the Python lane

Use Python 3.10+ (verified on Python 3.14). From the cloned repository, one command installs dependencies and runs the pipeline:

```sh
python -m pip install -r requirements.txt && python scraper.py
```

Output: `output/books.json`, `output/errors.json`, `output/run-report.json`. `python scraper.py --simulate-failure` injects a local broken URL, retains 60 books, and reports one failed page without unnecessary network traffic. `python -m pytest -q` runs nine offline checks.

Raw fields: title, product_url, price_text, availability_text, rating_text, description (nullable), source_page, fetched_at. Validated books also include numeric nonnegative price_gbp; text whitespace is collapsed, URLs require HTTPS, ratings must be One–Five. Original fetch timestamps survive cached reruns.

Politeness: identifying user-agent links this repo; 10-second timeout; explicit status checks; at least 0.5 seconds between real requests; one retry for timeout/server failures; disk caching; cache/ is ignored. A failed page is logged and skipped. No browser is needed because the book data is already in the HTML sent by the server. Prefer official APIs, never bypass login, paywalls or blocks, and collect only necessary public data.

Limitation: selectors depend on this sandbox's current HTML; catalogue failure may prevent discovering later pages. Cached content stays cached until cache/ is removed. No AI bonus or optional browser comparison is claimed.

Fresh cached run (the initial live stage fetched all 60 details; see stage3-live.log):

```json
{
  "started_at": "2026-11-05T07:37:10.615427+00:00",
  "duration_seconds": 0.748,
  "pages_fetched": 0,
  "cache_hits": 63,
  "catalogue_pages": 3,
  "unique_urls": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

See BUILDLOG.md for actual checkpoints recorded before each required stage commit. The original repository remains preserved.
