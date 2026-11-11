from fastapi import FastAPI, HTTPException, Response
from typing import List, Dict
import json
import logging
from src.config import settings
from src.core import db
from src.core.fetcher import SubscriptionFetcher
from src.core.parser import parse_upstream_json, ProxyNode
from src.core.checker import NodeHealthChecker, check_node
from src.generators.xray import generate_happ_subscription_json
from src.generators.profiles import generate_base64_subscription

logger = logging.getLogger(__name__)

app = FastAPI(title='ham-bot API', docs_url=None, redoc_url=None)

fetcher = SubscriptionFetcher(
    sub_url=settings.SUB_URL,
    hwid=settings.HWID,
    cache_ttl_hours=settings.CACHE_TTL_HOURS
)

checker = NodeHealthChecker(
    target_alive=settings.TARGET_ALIVE_NODES
)

async def get_current_nodes(only_alive: bool = True, force_fetch: bool = False) -> List[ProxyNode]:
    raw_data, _ = await fetcher.fetch(force=force_fetch)
    nodes = parse_upstream_json(raw_data, whitelist=settings.REGION_WHITELIST)

    if not only_alive:
        return nodes

    if checker.alive_nodes:
        first_node = checker.alive_nodes[0]
        if await check_node(first_node):
            return checker.alive_nodes

    alive = await checker.scan_pool(nodes, quick=True)
    if not alive:
        return nodes
    return alive

def verify_token(token: str):
    if token == settings.SUB_SECRET_TOKEN:
        return
    if db.is_valid_personal_token(token):
        return
    raise HTTPException(status_code=403, detail='Forbidden')

def get_proxy_headers() -> Dict[str, str]:
    headers = fetcher.load_headers()
    custom_headers = {}
    pass_keys = [
        'profile-title', 'profile-update-interval', 'subscription-userinfo',
        'announce', 'announce-url', 'support-url', 'profile-web-page-url',
        'x-hwid-active'
    ]
    for k in pass_keys:
        if k in headers:
            custom_headers[k] = headers[k]
    return custom_headers

@app.api_route('/s/{token}/all-smart', methods=['GET', 'HEAD'])
async def get_all_smart_json(token: str):
    verify_token(token)
    nodes = await get_current_nodes(only_alive=False)
    configs = generate_happ_subscription_json(nodes, sub_domain=settings.SUB_DOMAIN)
    return Response(
        content=json.dumps(configs, ensure_ascii=False, indent=2),
        media_type='application/json; charset=utf-8',
        headers=get_proxy_headers()
    )

@app.api_route('/s/{token}/verified-smart', methods=['GET', 'HEAD'])
async def get_verified_smart_json(token: str):
    verify_token(token)
    nodes = await get_current_nodes(only_alive=True)
    configs = generate_happ_subscription_json(nodes, sub_domain=settings.SUB_DOMAIN)
    return Response(
        content=json.dumps(configs, ensure_ascii=False, indent=2),
        media_type='application/json; charset=utf-8',
        headers=get_proxy_headers()
    )

@app.api_route('/s/{token}/verified-raw', methods=['GET', 'HEAD'])
async def get_verified_raw_base64(token: str):
    verify_token(token)
    nodes = await get_current_nodes(only_alive=True)
    b64_content = generate_base64_subscription(nodes)
    return Response(
        content=b64_content,
        media_type='text/plain; charset=utf-8',
        headers=get_proxy_headers()
    )
