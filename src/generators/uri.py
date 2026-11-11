import urllib.parse
import io
import qrcode
from src.core.parser import ProxyNode

def node_to_vless_uri(node: ProxyNode) -> str:
    params = {
        'encryption': 'none',
        'type': 'tcp',
        'security': node.security,
        'flow': node.flow,
        'sni': node.sni,
        'fp': node.fp
    }
    if node.alpn:
        params['alpn'] = ','.join(node.alpn)
        
    query_str = urllib.parse.urlencode(params)
    fragment = urllib.parse.quote(node.remarks)
    return f'vless://{node.uuid}@{node.address}:{node.port}?{query_str}#{fragment}'

def generate_qr_bytes(text: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()
