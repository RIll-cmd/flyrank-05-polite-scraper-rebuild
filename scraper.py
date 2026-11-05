import re
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

BASE = 'https://books.toscrape.com/'
CACHE = Path('cache')
HEADERS = {'User-Agent': 'FlyRankInternship-A9/1.0 (+https://github.com/RIll-cmd/flyrank-05-polite-scraper-rebuild)'}
FETCH_STATS = {'pages_fetched': 0, 'cache_hits': 0}

def fetch(url):
    if urlparse(url).hostname != 'books.toscrape.com' or urlparse(url).scheme != 'https':
        raise ValueError('URL outside sandbox')
    CACHE.mkdir(exist_ok=True)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + '.json')
    if path.exists():
        result = json.loads(path.read_text(encoding='utf8'))
        FETCH_STATS['cache_hits'] += 1
        print('CACHE HIT', url, len(result['html'].encode('utf8')))
        return result
    for attempt in range(2):
        time.sleep(0.5)
        try:
            response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=False)
            response.raise_for_status()
            if response.status_code != 200:
                raise requests.HTTPError(f'Unexpected HTTP status {response.status_code}', response=response)
            break
        except (requests.Timeout, requests.HTTPError) as error:
            if attempt or (isinstance(error, requests.HTTPError) and (error.response is None or error.response.status_code < 500)):
                raise
    response.encoding = 'utf8'
    result = {'html': response.text, 'fetched_at': datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(result, ensure_ascii=False), encoding='utf8')
    FETCH_STATS['pages_fetched'] += 1
    print('FETCH', url, len(response.content))
    return result

def discover(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    return [urljoin(url, a['href']) for a in soup.select('article.product_pod h3 a[href]')]

def discover_catalogue():
    url = BASE + 'catalogue/page-1.html'
    products = {}
    discovered = 0
    for number in range(3):
        page = fetch(url)
        links = discover(page['html'], url)
        discovered += len(links)
        for product in links:
            products.setdefault(product, url)
        next_link = BeautifulSoup(page['html'], 'html.parser').select_one('li.next a')
        if number < 2:
            if next_link is None:
                raise ValueError('missing next catalogue link')
            url = urljoin(url, next_link['href'])
    print(f'catalogue_pages=3 discovered={discovered} unique_urls={len(products)}')
    return products

def extract_raw(html, url, source, fetched_at):
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.select_one('.product_main')
    if main is None:
        raise ValueError('missing product area')
    marker = soup.select_one('#product_description')
    description = marker.find_next_sibling('p') if marker else None
    return {
        'title': main.select_one('h1').get_text(' ', strip=True),
        'product_url': url,
        'price_text': main.select_one('.price_color').get_text(strip=True),
        'availability_text': main.select_one('.availability').get_text(' ', strip=True),
        'rating_text': main.select_one('.star-rating')['class'][-1],
        'description': description.get_text(' ', strip=True) if description else None,
        'source_page': source,
        'fetched_at': fetched_at,
    }

def collect_raw():
    books = []
    for url, source in discover_catalogue().items():
        page = fetch(url)
        books.append(extract_raw(page['html'], url, source, page['fetched_at']))
    Path('output').mkdir(exist_ok=True)
    Path('output/raw-books.json').write_text(json.dumps(books, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(books[0], ensure_ascii=False))
    print(f'detail_pages={len(books)}')
    return books

class Book(BaseModel):
    title: str = Field(min_length=1)
    product_url: HttpUrl
    price_text: str
    price_gbp: float = Field(ge=0)
    availability_text: str = Field(min_length=1)
    rating_text: Literal['One', 'Two', 'Three', 'Four', 'Five']
    description: str | None
    source_page: HttpUrl
    fetched_at: datetime

    @field_validator('product_url', 'source_page')
    @classmethod
    def https_only(cls, value):
        if value.scheme != 'https':
            raise ValueError('HTTPS required')
        return value

def parse_price(value):
    if not re.fullmatch(r'£\d+\.\d{2}', value.strip()):
        raise ValueError('invalid GBP price')
    return float(value.strip()[1:])

def normalize(raw):
    cleaned = dict(raw)
    for key in ['title', 'availability_text', 'description']:
        if cleaned[key] is not None:
            cleaned[key] = ' '.join(cleaned[key].split())
    cleaned['price_gbp'] = parse_price(cleaned['price_text'])
    return Book(**cleaned).model_dump(mode='json')

def run():
    books = [normalize(raw) for raw in collect_raw()]
    Path('output/books.json').write_text(json.dumps(books, indent=2, ensure_ascii=False), encoding='utf8')
    print(f'valid_records={len(books)}')

if __name__ == '__main__':
    run()
