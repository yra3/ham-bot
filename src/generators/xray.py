import copy
import json
from typing import Dict, Any, List
from src.core.parser import ProxyNode, sanitize_and_patch_config

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

def generate_client_full_json(node: ProxyNode, sub_domain: str) -> Dict[str, Any]:
    return sanitize_and_patch_config(node.raw_config, sub_domain)

def generate_happ_subscription_json(nodes: List[ProxyNode], sub_domain: str) -> List[Dict[str, Any]]:
    configs = []
    for node in nodes:
        configs.append(sanitize_and_patch_config(node.raw_config, sub_domain))
    return configs
