import os
import time
import json
import logging
from typing import Tuple, List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache')
DATA_FILE = os.path.join(CACHE_DIR, 'body_happ_win.txt')
HEADERS_FILE = os.path.join(CACHE_DIR, 'headers_happ_win.txt')

class SubscriptionFetcher:
    def __init__(self, sub_url: str, hwid: str, cache_ttl_hours: int = 24):
        self.sub_url = sub_url
        self.hwid = hwid
        self.cache_ttl_seconds = cache_ttl_hours * 3600
        os.makedirs(CACHE_DIR, exist_ok=True)

    def is_cache_valid(self) -> bool:
        if not os.path.exists(DATA_FILE):
            return False
        mtime = os.path.getmtime(DATA_FILE)
        return (time.time() - mtime) < self.cache_ttl_seconds

    def load_from_cache(self) -> Optional[List[Dict[str, Any]]]:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f'Failed to read cache file: {e}')
        return None

    def load_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if os.path.exists(HEADERS_FILE):
            try:
                with open(HEADERS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        if ':' in line:
                            k, v = line.split(':', 1)
                            headers[k.strip().lower()] = v.strip()
            except Exception as e:
                logger.warning(f'Could not parse headers file: {e}')
        return headers

    async def fetch(self, force: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        if not force and self.is_cache_valid():
            cached = self.load_from_cache()
            if cached:
                return cached, self.load_headers()

        headers = {
            'User-Agent': 'Happ/2.4.0',
            'X-HWID': self.hwid,
            'X-Device-OS': 'Windows',
            'X-Ver-OS': '10.0.22631',
            'X-Device-Model': 'Desktop-PC'
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.get(self.sub_url, headers=headers)
            resp.raise_for_status()

            resp_headers_dict = dict(resp.headers)
            with open(HEADERS_FILE, 'w', encoding='utf-8') as f:
                for k, v in resp_headers_dict.items():
                    f.write(k + ': ' + str(v) + chr(10))

            data = resp.json()
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return data, resp_headers_dict
