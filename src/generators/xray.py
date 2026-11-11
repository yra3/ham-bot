import copy
import json
import logging
import os
from typing import Dict, Any, List
from src.core.parser import ProxyNode, sanitize_and_patch_config, parse_upstream_json

logger = logging.getLogger(__name__)

def generate_router_outbound_json(node: ProxyNode) -> Dict[str, Any]:
    # Extract just the proxy outbound block for the router
    outbounds = node.raw_config.get('outbounds', [])
    proxy = next((o for o in outbounds if o.get('tag') == 'proxy'), None)
    if proxy:
        return copy.deepcopy(proxy)
        
    # Fallback to building clean outbound
    return {
        'protocol': 'vless',
        'tag': 'proxy',
        'settings': {
            'vnext': [{
                'address': node.address,
                'port': node.port,
                'users': [{
                    'id': node.uuid,
                    'encryption': 'none',
                    'flow': node.flow
                }]
            }]
        },
        'streamSettings': {
            'network': 'tcp',
            'security': node.security,
            'tcpSettings': {},
            'tlsSettings': {
                'allowInsecure': False,
                'alpn': node.alpn,
                'fingerprint': node.fp,
                'serverName': node.sni,
                'show': False
            }
        }
    }

def generate_client_full_json(
    node: ProxyNode,
    sub_domain: str,
    direct_domains: List[str] = None,
) -> Dict[str, Any]:
    return sanitize_and_patch_config(node.raw_config, sub_domain, direct_domains=direct_domains)

def generate_happ_subscription_json(
    nodes: List[ProxyNode],
    sub_domain: str,
    direct_domains: List[str] = None,
) -> List[Dict[str, Any]]:
    configs = []
    for node in nodes:
        configs.append(sanitize_and_patch_config(node.raw_config, sub_domain, direct_domains=direct_domains))
    return configs

def generate_sidecar_xray_config(nodes: List[ProxyNode], socks_port: int = 10808) -> Dict[str, Any]:
    outbounds: List[Dict[str, Any]] = []
    for idx, node in enumerate(nodes[:5]):
        ob = generate_router_outbound_json(node)
        ob['tag'] = f'proxy-{idx}'
        outbounds.append(ob)

    outbounds.append({'tag': 'direct', 'protocol': 'freedom'})

    return {
        'log': {'loglevel': 'warning'},
        'inbounds': [{
            'tag': 'socks-in',
            'port': socks_port,
            'listen': '0.0.0.0',
            'protocol': 'socks',
            'settings': {'auth': 'noauth', 'udp': True},
            'sniffing': {'enabled': True, 'destOverride': ['http', 'tls', 'quic']}
        }],
        'outbounds': outbounds,
        'burstObservatory': {
            'subjectSelector': ['proxy-'],
            'pingConfig': {
                'destination': 'https://www.gstatic.com/generate_204',
                'interval': '2m',
                'sampling': 2,
                'timeout': '5s'
            }
        },
        'routing': {
            'balancers': [{
                'tag': 'proxy-balancer',
                'selector': ['proxy-'],
                'strategy': {'type': 'leastPing'}
            }],
            'rules': [{
                'type': 'field',
                'inboundTag': ['socks-in'],
                'balancerTag': 'proxy-balancer'
            }]
        }
    }

async def sync_sidecar_xray_config(fetcher, checker, whitelist: List[str]) -> bool:
    try:
        raw_data, _ = await fetcher.fetch()
        nodes = parse_upstream_json(raw_data, whitelist=whitelist)
        if not nodes:
            nodes = parse_upstream_json(raw_data, whitelist=None)
        if not nodes:
            logger.warning('No valid nodes found to generate sidecar xray config.')
            return False

        selected = checker.alive_nodes[:5] if checker.alive_nodes else nodes[:5]
        cfg = generate_sidecar_xray_config(selected)

        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'xray')
        os.makedirs(data_dir, exist_ok=True)
        cfg_path = os.path.join(data_dir, 'config.json')
        tmp_path = cfg_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, cfg_path)
        logger.info(f'Sidecar xray config written with {len(selected)} nodes: {cfg_path}')
        return True
    except Exception as e:
        logger.error(f'Failed to generate sidecar xray config: {e}')
        return False
