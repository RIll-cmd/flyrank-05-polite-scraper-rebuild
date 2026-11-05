# Rebuild checkpoint log

All checks occurred during the current rebuild before the corresponding commit. Existing work was consulted as a reference.

## Stage 0
2026-11-05T07:29:54.877212+00:00 — Python requests GET https://toscrape.com/ → 200, sandbox text present. GET https://books.toscrape.com/robots.txt → 404. README scope and required pledge verified. Public GitHub repository was created before implementation.

## Stage 1
2026-11-05T07:30:22.660702+00:00 — `python scraper.py` twice:
```text
FETCH https://books.toscrape.com/catalogue/page-1.html 50469
CACHE HIT https://books.toscrape.com/catalogue/page-1.html 50469
```

## Stage 2
2026-11-05T07:30:48.507026+00:00 — `python scraper.py` twice:
```text
CACHE HIT https://books.toscrape.com/catalogue/page-1.html 50469
FETCH https://books.toscrape.com/catalogue/page-2.html 50877
FETCH https://books.toscrape.com/catalogue/page-3.html 51374
catalogue_pages=3 discovered=60 unique_urls=60
CACHE HIT https://books.toscrape.com/catalogue/page-1.html 50469
CACHE HIT https://books.toscrape.com/catalogue/page-2.html 50877
CACHE HIT https://books.toscrape.com/catalogue/page-3.html 51374
catalogue_pages=3 discovered=60 unique_urls=60
```

## Stage 3
2026-11-05T07:33:36.728054+00:00 — `python scraper.py` fetched 60 detail pages live. Exactly 60 raw records with eight keys; optional description may be null. Full fetch trace in stage3-live.log. Example:
```json
{"title": "A Light in the Attic", "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html", "price_text": "£51.77", "availability_text": "In stock (22 available)", "rating_text": "Three", "description": "It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition. Silverstein's humorous and creative verse can amuse the dowdiest of readers. Lemon-faced adults and fidgety kids sit still and read these rhythmic words and laugh and smile and love th It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition. Silverstein's humorous and creative verse can amuse the dowdiest of readers. Lemon-faced adults and fidgety kids sit still and read these rhythmic words and laugh and smile and love that Silverstein. Need proof of his genius? RockabyeRockabye baby, in the treetopDon't you know a treetopIs no safe place to rock?And who put you up there,And your cradle, too?Baby, I think someone down here'sGot it in for you. Shel, you never sounded so good. ...more", "source_page": "https://books.toscrape.com/catalogue/page-1.html", "fetched_at": "2026-11-05T07:31:07.908596+00:00"}
```

## Stage 4
2026-11-05T07:34:15.463524+00:00 — `python scraper.py` twice; JSON assertions:
Run 1: 60 valid records, numeric prices, HTTPS URLs, 63 cache hits
Run 2: 60 valid records, numeric prices, HTTPS URLs, 63 cache hits

## Stage 5
2026-11-05T07:35:50.923141+00:00 — `python scraper.py` then `python scraper.py --simulate-failure`; both retained all 60 good books; injected fake URL recorded and skipped. Reports:
```json
[
  {
    "started_at": "2026-11-05T07:35:46.432123+00:00",
    "duration_seconds": 2.459,
    "pages_fetched": 0,
    "cache_hits": 63,
    "catalogue_pages": 3,
    "unique_urls": 60,
    "valid_records": 60,
    "invalid_records": 0,
    "failed_pages": 0
  },
  {
    "started_at": "2026-11-05T07:35:50.008998+00:00",
    "duration_seconds": 0.819,
    "pages_fetched": 0,
    "cache_hits": 63,
    "catalogue_pages": 3,
    "unique_urls": 61,
    "valid_records": 60,
    "invalid_records": 0,
    "failed_pages": 1
  }
]
```
Rechecked after adding catalogue-page error isolation: 60 valid, 1 simulated failed page; catalogue count remains actual (3).

## Stage 6
2026-11-05T07:37:11.437661+00:00 — `python -m pytest -q`: 9 passed. `python scraper.py`: 60 valid, zero failures, 63 cache hits. README run command and schema checked; sample outputs included, cache excluded. Seven required stage commits will be present after this checkpoint commit.
