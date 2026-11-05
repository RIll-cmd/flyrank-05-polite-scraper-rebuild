import json
import requests
import pytest
import scraper

HTML = '''<div class="product_main"><h1>  Test   book </h1><p class="price_color">£12.34</p><p class="availability"> In  stock </p><p class="star-rating Three"></p></div>'''
URL = scraper.BASE + 'catalogue/test/index.html'
SOURCE = scraper.BASE + 'catalogue/page-1.html'
STAMP = '2026-11-05T00:00:00+00:00'

def raw():
    return scraper.extract_raw(HTML, URL, SOURCE, STAMP)

def test_optional_description_and_raw_receipt():
    record = raw()
    assert len(record) == 8
    assert record['description'] is None
    assert record['fetched_at'] == STAMP
    assert record['source_page'] == SOURCE

def test_product_area_avoids_unrelated_price():
    record = scraper.extract_raw('<p class="price_color">£99.99</p>' + HTML, URL, SOURCE, STAMP)
    assert record['price_text'] == '£12.34'

def test_normalizes_whitespace_and_price():
    record = scraper.normalize(raw())
    assert record['title'] == 'Test book'
    assert record['availability_text'] == 'In stock'
    assert record['price_gbp'] == 12.34

def test_rejects_bad_price():
    for value in ['free', '£-1.00', '$12.34', '£12']:
        with pytest.raises(ValueError):
            scraper.parse_price(value)

def test_rejects_http_and_unknown_rating():
    record = raw()
    record['product_url'] = 'http://books.toscrape.com/test'
    with pytest.raises(ValueError):
        scraper.normalize(record)
    record = raw()
    record['rating_text'] = 'Six'
    with pytest.raises(ValueError):
        scraper.normalize(record)

def test_discovery_resolves_relative_urls():
    html = '<article class="product_pod"><h3><a href="test/index.html">Book</a></h3></article>'
    assert scraper.discover(html, SOURCE) == [URL]

def test_cache_preserves_fetch_time_without_network(tmp_path, monkeypatch):
    monkeypatch.setattr(scraper, 'CACHE', tmp_path)
    class Response:
        status_code = 200
        text = HTML
        content = HTML.encode()
        def raise_for_status(self): pass
    monkeypatch.setattr(scraper.requests, 'get', lambda *a, **kw: Response())
    monkeypatch.setattr(scraper.time, 'sleep', lambda _: None)
    first = scraper.fetch(URL)
    def unexpected(*args, **kwargs): raise AssertionError('network used for cache hit')
    monkeypatch.setattr(scraper.requests, 'get', unexpected)
    assert scraper.fetch(URL) == first

def test_partial_catalogue_survives_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def broken(url): raise requests.ConnectionError('offline')
    monkeypatch.setattr(scraper, 'fetch', broken)
    report = scraper.run()
    assert report['failed_pages'] == 1
    assert report['catalogue_pages'] == 0
    assert json.loads((tmp_path / 'output/books.json').read_text()) == []

def test_bad_detail_does_not_discard_good_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def catalogue(errors):
        scraper.FETCH_STATS['catalogue_pages'] = 3
        return {URL: SOURCE, scraper.BASE + 'bad': SOURCE}
    monkeypatch.setattr(scraper, 'discover_catalogue', catalogue)
    def fetch(url):
        if url.endswith('bad'): raise requests.HTTPError('404')
        return {'html': HTML, 'fetched_at': STAMP}
    monkeypatch.setattr(scraper, 'fetch', fetch)
    report = scraper.run()
    assert report['valid_records'] == 1
    assert report['failed_pages'] == 1
    assert len(json.loads((tmp_path / 'output/books.json').read_text())) == 1
