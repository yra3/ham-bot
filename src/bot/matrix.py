import asyncio
import hashlib
import logging
import io
import json
import os
import re
import urllib.parse
import httpx
from src.config import settings
from src.core.fetcher import SubscriptionFetcher
from src.core.parser import parse_upstream_json, ProxyNode
from src.core.checker import NodeHealthChecker, check_node
from src.generators.uri import node_to_vless_uri, generate_qr_bytes
from src.generators.xray import generate_router_outbound_json, generate_client_full_json
from src.bot.content import build_matrix_welcome_html, build_matrix_apps_html

logger = logging.getLogger('matrix-bot')

fetcher = SubscriptionFetcher(
    sub_url=settings.SUB_URL,
    hwid=settings.HWID,
    cache_ttl_hours=settings.CACHE_TTL_HOURS
)

checker = NodeHealthChecker(
    target_alive=settings.TARGET_ALIVE_NODES
)

async def get_working_node() -> ProxyNode:
    raw_data, _ = await fetcher.fetch()
    nodes = parse_upstream_json(raw_data, whitelist=settings.REGION_WHITELIST)
    if not nodes:
        return None
    # Check cached alive nodes first (in order), returning the first that actually responds right now
    for candidate in checker.alive_nodes:
        if await check_node(candidate):
            return candidate
    # Otherwise scan the pool until 1 working node is found
    for node in nodes:
        if await check_node(node):
            if node not in checker.alive_nodes:
                checker.alive_nodes.append(node)
            return node
    return nodes[0]

async def get_working_nodes_list(limit: int = 5) -> list:
    raw_data, _ = await fetcher.fetch()
    nodes = parse_upstream_json(raw_data, whitelist=settings.REGION_WHITELIST)
    if not nodes:
        return []
    if checker.alive_nodes and await check_node(checker.alive_nodes[0]):
        return checker.alive_nodes[:limit]
    alive = await checker.scan_pool(nodes, quick=True)
    return (alive or nodes)[:limit]

class MatrixBotService:
    def __init__(self):
        self.homeserver = settings.MATRIX_HOMESERVER.rstrip('/')
        self.user_id = settings.MATRIX_USER_ID
        self.token = settings.MATRIX_ACCESS_TOKEN
        self.next_batch = ''

    async def api_req(self, method: str, path: str, json_data: dict = None, params: dict = None) -> dict:
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        async with httpx.AsyncClient(timeout=35.0) as client:
            url = f'{self.homeserver}{path}'
            resp = await client.request(method, url, json=json_data, params=params, headers=headers)
            if resp.status_code >= 400:
                logger.error(f'Matrix API error {resp.status_code}: {resp.text}')
                return {}
            try:
                return resp.json()
            except Exception as e:
                logger.error(f'Failed to parse Matrix response ({resp.status_code}): {resp.text[:200]}')
                return {}

    async def send_message(self, room_id: str, html_body: str):
        plain = html_body.replace('<br>', chr(10))
        plain = re.sub(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', r'\2 (\1)', plain)
        plain = re.sub(r'<[^>]+>', '', plain)
        data = {
            'msgtype': 'm.text',
            'body': plain,
            'format': 'org.matrix.custom.html',
            'formatted_body': html_body
        }
        txn_id = int(asyncio.get_event_loop().time() * 1000)
        await self.api_req('PUT', f'/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn_id}', json_data=data)

    async def send_file(self, room_id: str, filename: str, data: bytes, mime_type: str):
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': mime_type
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f'{self.homeserver}/_matrix/media/v3/upload',
                params={'filename': filename},
                content=data,
                headers=headers
            )
            if resp.status_code != 200:
                logger.error(f'Failed to upload file to Matrix: {resp.text}')
                return
            mxc_url = resp.json().get('content_uri')

        msgtype = 'm.image' if mime_type.startswith('image/') else 'm.file'
        txn_id = int(asyncio.get_event_loop().time() * 1000)
        payload = {
            'msgtype': msgtype,
            'body': filename,
            'url': mxc_url,
            'info': {'mimetype': mime_type, 'size': len(data)}
        }
        await self.api_req('PUT', f'/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn_id}', json_data=payload)

    async def join_room(self, room_id: str):
        await self.api_req('POST', f'/_matrix/client/v3/rooms/{room_id}/join')

    async def ensure_avatar(self):
        avatar_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'assets',
            'avatar.jpg'
        )
        if not os.path.exists(avatar_path):
            logger.warning(f'Avatar file not found at {avatar_path}')
            return

        with open(avatar_path, 'rb') as f:
            avatar_bytes = f.read()

        current_hash = hashlib.sha256(avatar_bytes).hexdigest()
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        hash_file = os.path.join(data_dir, 'avatar.sha256')

        encoded_uid = urllib.parse.quote(self.user_id, safe='')
        profile_res = await self.api_req('GET', f'/_matrix/client/v3/profile/{encoded_uid}/avatar_url')
        existing_avatar = profile_res.get('avatar_url')

        if existing_avatar and os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                if f.read().strip() == current_hash:
                    return

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f'{self.homeserver}/_matrix/media/v3/upload',
                params={'filename': 'avatar.jpg'},
                content=avatar_bytes,
                headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'image/jpeg'}
            )
            if resp.status_code != 200:
                logger.error(f'Failed to upload avatar to Matrix: {resp.status_code} {resp.text}')
                return
            mxc_url = resp.json().get('content_uri')

        if mxc_url:
            await self.api_req(
                'PUT',
                f'/_matrix/client/v3/profile/{encoded_uid}/avatar_url',
                json_data={'avatar_url': mxc_url}
            )
            with open(hash_file, 'w') as f:
                f.write(current_hash)
            logger.info(f'Bot avatar updated: {mxc_url}')

    async def handle_command(self, room_id: str, sender: str, text: str):
        body = text.strip()
        cmd = body.split()[0].lower() if body else ''
        is_admin = sender in settings.MATRIX_ADMIN_USERS
        if is_admin:
            from src.core import db
            if not db.get_meta(f'matrix_dm:{sender}'):
                db.set_meta(f'matrix_dm:{sender}', room_id)

        if cmd in ['!help', '!start', 'помощь', 'привет', 'старт', 'help']:
            smart_url = settings.build_sub_url(settings.SUB_SECRET_TOKEN, 'verified-smart')
            msg = build_matrix_welcome_html(smart_url, is_admin=is_admin)
            await self.send_message(room_id, msg)

        elif cmd == '!apps':
            await self.send_message(room_id, build_matrix_apps_html())

        elif cmd == '!happ':
            smart_url = settings.build_sub_url(settings.SUB_SECRET_TOKEN, 'verified-smart')
            msg = (
                '⭐ <b>Ссылка на автоподписку (Happ — рекомендуемое приложение):</b><br><br>'
                f'<code>{smart_url}</code><br><br>'
                '<b>Как использовать:</b><br>'
                '1. Скопируй ссылку выше.<br>'
                '2. Открой приложение <b>Happ</b>.<br>'
                '3. Нажми <b>«+» ➔ «Добавить из ссылки»</b>, вставь её и нажми <b>«Обновить»</b>.'
            )
            await self.send_message(room_id, msg)

        elif cmd == '!vless':
            node = await get_working_node()
            if not node:
                await self.send_message(room_id, '⚠️ Нет доступных серверов.')
                return
            uri = node_to_vless_uri(node)
            msg = (
                '🔗 <b>Прямая ссылка на проверенный сервер:</b><br>'
                f'📍 <b>Локация:</b> {node.remarks}<br><br>'
                f'<code>{uri}</code>'
            )
            await self.send_message(room_id, msg)

        elif cmd == '!raw':
            working = await get_working_nodes_list(limit=5)
            if not working:
                await self.send_message(room_id, '⚠️ Нет доступных серверов.')
                return
            lines = [f'• {n.remarks}<br><code>{node_to_vless_uri(n)}</code>' for n in working]
            msg = '🔗 <b>Список vless ссылок:</b><br><br>' + '<br><br>'.join(lines)
            await self.send_message(room_id, msg)

        elif cmd == '!qr':
            node = await get_working_node()
            uri = node_to_vless_uri(node)
            qr_bytes = generate_qr_bytes(uri)
            await self.send_message(room_id, f'📸 <b>QR-код для подключения: {node.remarks}</b><br>Отсканируй камерой или из приложения:')
            await self.send_file(room_id, 'vpn_qr.png', qr_bytes, 'image/png')

        elif cmd == '!router':
            node = await get_working_node()
            outbound_json = generate_router_outbound_json(node)
            json_bytes = json.dumps(outbound_json, indent=2, ensure_ascii=False).encode('utf-8')
            await self.send_message(room_id, f'🌐 <b>Конфигурация для роутера (Keenetic Xray):</b><br>Сервер: {node.remarks}')
            await self.send_file(room_id, 'proxy-outbound.json', json_bytes, 'application/json')

        elif cmd == '!all':
            all_url = settings.build_sub_url(settings.SUB_SECRET_TOKEN, 'all-smart')
            msg = f'🌐 <b>Ссылка со всеми резервными серверами (JSON):</b><br><br><code>{all_url}</code>'
            await self.send_message(room_id, msg)

        elif cmd == '!admin':
            if not is_admin:
                await self.send_message(room_id, '⛔ У вас нет прав администратора.')
                return

            args = body.split()[1:] if len(body.split()) > 1 else []
            sub_cmd = args[0].lower() if args else ''

            if sub_cmd == 'force_refresh':
                from src.generators.xray import sync_sidecar_xray_config
                await self.send_message(room_id, '⏳ Принудительно запрашиваю свежую подписку с апстрима...')
                data, _ = await fetcher.fetch(force=True)
                nodes = parse_upstream_json(data, whitelist=settings.REGION_WHITELIST)
                checker.alive_nodes = []
                alive = await checker.scan_pool(nodes, quick=True)
                await sync_sidecar_xray_config(fetcher, checker, settings.REGION_WHITELIST)
                await self.send_message(room_id, f'✅ Подписка обновлена! Валидных нод: {len(nodes)}, подтверждено живых: {len(alive)}.')

            elif sub_cmd == 'check':
                await self.send_message(room_id, '🔍 Запускаю проверку доступности узлов...')
                raw_data, _ = await fetcher.fetch()
                nodes = parse_upstream_json(raw_data, whitelist=settings.REGION_WHITELIST)
                alive = await checker.scan_pool(nodes, quick=True)
                alive_list = '<br>'.join([f'• {n.remarks} ({n.address}:{n.port})' for n in alive])
                await self.send_message(room_id, f'✅ Проверка завершена! Доступно: {len(alive)}/{len(nodes)}:<br>{alive_list}')

            elif sub_cmd == 'status':
                is_valid = fetcher.is_cache_valid()
                alive_cnt = len(checker.alive_nodes)
                is_act = "Актуален ✅" if is_valid else "Устарел / отсутствует ⚠️"
                msg = (
                    '📊 <b>Диагностика системы:</b><br>'
                    f'• Кэш подписки: {is_act}<br>'
                    f'• Подтвержденных живых серверов: <b>{alive_cnt}</b><br>'
                    f'• Целевой лимит (TARGET_ALIVE_NODES): <b>{settings.TARGET_ALIVE_NODES}</b><br>'
                    f'• Белый список регионов: <code>{", ".join(settings.REGION_WHITELIST)}</code>'
                )
                await self.send_message(room_id, msg)

            elif sub_cmd == 'tg_invite':
                from src.core import db
                code = db.create_invite(created_by=sender, ttl_hours=24)
                bot_username = db.get_meta('tg_bot_username')
                link_part = (
                    f'<br><br>🔗 <b>Ссылка:</b> <code>https://t.me/{bot_username}?start={code}</code>'
                    if bot_username else ''
                )
                msg = (
                    '🎟️ <b>Одноразовое приглашение в Telegram создано (действует 24ч):</b><br><br>'
                    f'Команда для бота: <code>/start {code}</code>'
                    f'{link_part}'
                )
                await self.send_message(room_id, msg)

            elif sub_cmd == 'tg_users':
                from src.core import db
                users = db.list_tg_users()
                if not users:
                    await self.send_message(room_id, '📭 Авторизованных пользователей Telegram пока нет.')
                else:
                    lines = []
                    for u in users:
                        st = '✅' if u['is_active'] else '🚫'
                        uname = f"@{u['username']}" if u['username'] else u['full_name'] or 'без имени'
                        lines.append(f"{st} <code>{u['user_id']}</code> ({uname})")
                    await self.send_message(room_id, '👥 <b>Пользователи Telegram:</b><br>' + '<br>'.join(lines))

            elif sub_cmd == 'tg_revoke':
                from src.core import db
                if len(args) < 2 or not args[1].isdigit():
                    await self.send_message(room_id, 'Укажите числовой ID: <code>!admin tg_revoke 123456789</code>')
                else:
                    ok = db.revoke_tg_user(int(args[1]))
                    if ok:
                        await self.send_message(room_id, f'🚫 Доступ и подписка пользователя <code>{args[1]}</code> отозваны.')
                    else:
                        await self.send_message(room_id, f'Пользователь <code>{args[1]}</code> не найден в базе.')

            else:
                await self.send_message(
                    room_id,
                    '❓ Доступные опции: <code>!admin force_refresh</code>, <code>!admin check</code>, <code>!admin status</code>, '
                    '<code>!admin tg_invite</code>, <code>!admin tg_users</code>, <code>!admin tg_revoke &lt;id&gt;</code>.'
                )

    async def start(self):
        if not self.homeserver or not self.user_id or not self.token:
            logger.error('Matrix bot configuration incomplete (MATRIX_HOMESERVER / MATRIX_USER_ID / MATRIX_ACCESS_TOKEN). Skipping Matrix bot.')
            return
        logger.info(f'Starting Native HTTP Matrix Bot for {self.user_id} at {self.homeserver}...')
        await self.ensure_avatar()
        # Initial sync to skip ancient backlog
        init_data = await self.api_req('GET', '/_matrix/client/v3/sync', params={'timeout': 0})
        self.next_batch = init_data.get('next_batch', '')
        logger.info(f'Initial sync complete! Listening for invites and messages...')

        while True:
            try:
                params = {'timeout': 30000}
                if self.next_batch:
                    params['since'] = self.next_batch

                data = await self.api_req('GET', '/_matrix/client/v3/sync', params=params)
                if not data:
                    await asyncio.sleep(3)
                    continue

                self.next_batch = data.get('next_batch', self.next_batch)

                rooms = data.get('rooms', {})
                # 1. Handle Invites
                invite_rooms = rooms.get('invite', {})
                for room_id in invite_rooms:
                    logger.info(f'Auto-joining room on invite: {room_id}')
                    await self.join_room(room_id)
                    await asyncio.sleep(1)
                    smart_url = settings.build_sub_url(settings.SUB_SECRET_TOKEN, 'verified-smart')
                    await self.send_message(room_id, build_matrix_welcome_html(smart_url, is_admin=False))

                # 2. Handle Joined Room Messages
                join_rooms = rooms.get('join', {})
                for room_id, rdata in join_rooms.items():
                    timeline = rdata.get('timeline', {})
                    events = timeline.get('events', [])
                    for ev in events:
                        if ev.get('type') == 'm.room.message' and ev.get('sender') != self.user_id:
                            content = ev.get('content', {})
                            if content.get('msgtype') == 'm.text':
                                text = content.get('body', '')
                                sender = ev.get('sender')
                                # Run command in background task so sync loop never blocks
                                asyncio.create_task(self.handle_command(room_id, sender, text))

            except Exception as e:
                logger.error(f'Matrix sync loop exception: {e}', exc_info=True)
                await asyncio.sleep(3)
