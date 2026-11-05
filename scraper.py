import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests

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

if __name__ == '__main__':
    fetch(BASE + 'catalogue/page-1.html')
