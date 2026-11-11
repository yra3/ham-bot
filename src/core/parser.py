from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import urllib.parse
import re
import copy

@dataclass
class ProxyNode:
    remarks: str
    address: str
    port: int
    uuid: str
    flow: str
    security: str
    sni: str
    fp: str
    alpn: List[str]
    raw_config: Dict[str, Any]

def is_advertisement_or_promo(remarks: str) -> bool:
    promo_markers = [
        'нет обхода', 'белых списков', 'в основном', 'в нашем боте',
        'на пробном', 'подписке при покупке', 'купить', 'он есть в основной'
    ]
    r_lower = remarks.lower()
    return any(m in r_lower for m in promo_markers)

def is_obhod(remarks: str) -> bool:
    # 'Обход' means limited traffic
    return 'обход' in remarks.lower()

def matches_whitelist(remarks: str, whitelist: List[str]) -> bool:
    if not whitelist:
        return True
    return any(country.lower() in remarks.lower() for country in whitelist)

def parse_upstream_json(raw_items: List[Dict[str, Any]], whitelist: Optional[List[str]] = None) -> List[ProxyNode]:
    nodes: List[ProxyNode] = []
    
    for item in raw_items:
        remarks = item.get('remarks', '')
        if not remarks or is_advertisement_or_promo(remarks):
            continue
        if is_obhod(remarks):
            continue
        if whitelist is not None and not matches_whitelist(remarks, whitelist):
            continue
            
        outbounds = item.get('outbounds', [])
        proxy_outbound = next((o for o in outbounds if o.get('tag') == 'proxy' and o.get('protocol') == 'vless'), None)
        if not proxy_outbound:
            continue
            
        settings = proxy_outbound.get('settings', {})
        vnext = settings.get('vnext', [])
        if not vnext:
            continue
            
        target = vnext[0]
        address = target.get('address')
        port = target.get('port')
        users = target.get('users', [])
        if not address or not port or not users:
            continue
            
        user = users[0]
        uuid = user.get('id')
        flow = user.get('flow', 'xtls-rprx-vision')
        
        stream = proxy_outbound.get('streamSettings', {})
        security = stream.get('security', 'tls')
        
        if security == 'tls':
            tls_settings = stream.get('tlsSettings', {})
            sni = tls_settings.get('serverName', address)
            fp = tls_settings.get('fingerprint', 'firefox')
            alpn = tls_settings.get('alpn', ['h2', 'http/1.1'])
        elif security == 'reality':
            reality_settings = stream.get('realitySettings', {})
            sni = reality_settings.get('serverName', address)
            fp = reality_settings.get('fingerprint', 'firefox')
            alpn = reality_settings.get('alpn', ['h2', 'http/1.1'])
        else:
            sni = address
            fp = 'firefox'
            alpn = ['h2', 'http/1.1']
            
        nodes.append(ProxyNode(
            remarks=remarks,
            address=address,
            port=int(port),
            uuid=uuid,
            flow=flow,
            security=security,
            sni=sni,
            fp=fp,
            alpn=alpn,
            raw_config=item
        ))
        
    return nodes

def _normalize_domain_rule(entry: str) -> str:
    d = entry.strip()
    if not d:
        return ''
    if ':' in d:
        return d
    if d.startswith('*.'):
        d = d[2:]
    return f'domain:{d}'


def sanitize_and_patch_config(
    item: Dict[str, Any],
    sub_domain: str = '',
    direct_domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    config = copy.deepcopy(item)
    if not direct_domains:
        return config

    normalized: List[str] = []
    for entry in direct_domains:
        rule_dom = _normalize_domain_rule(entry)
        if rule_dom and rule_dom not in normalized:
            normalized.append(rule_dom)

    if not normalized:
        return config

    routing = config.setdefault('routing', {})
    rules = routing.setdefault('rules', [])
    rules.insert(0, {
        'type': 'field',
        'domain': normalized,
        'outboundTag': 'direct',
    })
    return config
