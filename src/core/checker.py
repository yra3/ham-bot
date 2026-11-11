import asyncio
import ssl
import time
import logging
from typing import List, Dict, Any, Optional
from src.core.parser import ProxyNode

logger = logging.getLogger(__name__)

async def check_tcp_port(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def check_tls_handshake(host: str, port: int, sni: str, timeout: float = 5.0) -> bool:
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=ctx, server_hostname=sni),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def check_node(node: ProxyNode) -> bool:
    # First check basic TCP
    tcp_ok = await check_tcp_port(node.address, node.port)
    if not tcp_ok:
        return False
    # If TLS security, check TLS handshake with SNI
    if node.security == 'tls':
        return await check_tls_handshake(node.address, node.port, node.sni)
    return True

class NodeHealthChecker:
    def __init__(self, target_alive: int = 5, batch_size: int = 2, batch_delay_s: float = 300.0):
        self.target_alive = target_alive  # -1 means check all
        self.batch_size = batch_size
        self.batch_delay_s = batch_delay_s
        self.alive_nodes: List[ProxyNode] = []
        self.last_check_time: float = 0.0
        self.is_running: bool = False

    async def scan_pool(self, nodes: List[ProxyNode], quick: bool = False) -> List[ProxyNode]:
        self.is_running = True
        alive: List[ProxyNode] = []
        
        try:
            for i in range(0, len(nodes), self.batch_size):
                batch = nodes[i:i + self.batch_size]
                results = await asyncio.gather(*(check_node(n) for n in batch))
                
                for node, is_ok in zip(batch, results):
                    if is_ok:
                        alive.append(node)
                        logger.info(f'Node is alive: {node.remarks} ({node.address}:{node.port})')
                    else:
                        logger.warning(f'Node failed health check: {node.remarks} ({node.address}:{node.port})')

                # If we reached target and not set to -1 (all)
                if self.target_alive != -1 and len(alive) >= self.target_alive:
                    break

                # If there are more nodes to check, delay between batches (skip delay if quick=True)
                if i + self.batch_size < len(nodes) and not quick:
                    await asyncio.sleep(self.batch_delay_s)
                    
            self.alive_nodes = alive
            self.last_check_time = time.time()
            return alive
        finally:
            self.is_running = False
