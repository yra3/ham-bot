import base64
from typing import List
from src.core.parser import ProxyNode
from src.generators.uri import node_to_vless_uri

def generate_base64_subscription(nodes: List[ProxyNode]) -> str:
    lines = [node_to_vless_uri(n) for n in nodes]
    raw_text = chr(10).join(lines)
    return base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
