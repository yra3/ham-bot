import logging
import time
from typing import Dict
import httpx
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from src.config import settings
from src.core import db

logger = logging.getLogger(__name__)

_last_notified: Dict[str, float] = {}


async def _send_matrix_dm(user_id: str, html_text: str) -> None:
    homeserver = settings.MATRIX_HOMESERVER.rstrip('/')
    token = settings.MATRIX_ACCESS_TOKEN
    if not homeserver or not token:
        return

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    meta_key = f'matrix_dm:{user_id}'
    room_id = db.get_meta(meta_key)

    async with httpx.AsyncClient(timeout=20.0) as client:
        if not room_id:
            resp = await client.post(
                f'{homeserver}/_matrix/client/v3/createRoom',
                json={
                    'invite': [user_id],
                    'is_direct': True,
                    'preset': 'trusted_private_chat',
                },
                headers=headers,
            )
            if resp.status_code < 400:
                room_id = resp.json().get('room_id')
                if room_id:
                    db.set_meta(meta_key, room_id)

        if not room_id:
            logger.warning(f'Could not obtain Matrix DM room for admin {user_id}')
            return

        plain = (
            html_text.replace('<b>', '')
            .replace('</b>', '')
            .replace('<code>', '')
            .replace('</code>', '')
            .replace('<br>', '\n')
        )
        txn_id = int(time.time() * 1000)
        send_resp = await client.put(
            f'{homeserver}/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn_id}',
            json={
                'msgtype': 'm.text',
                'body': plain,
                'format': 'org.matrix.custom.html',
                'formatted_body': html_text,
            },
            headers=headers,
        )
        if send_resp.status_code >= 400:
            # Room might have been left/forgotten; clear cached room_id
            db.set_meta(meta_key, '')
            logger.error(f'Failed sending Matrix admin alert to {user_id}: {send_resp.text}')


async def _send_telegram_dm(chat_id: int, html_text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    session = AiohttpSession(proxy=settings.TELEGRAM_PROXY_URL) if settings.TELEGRAM_PROXY_URL else None
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        await bot.send_message(chat_id=chat_id, text=html_text)
    except Exception as e:
        logger.error(f'Failed sending Telegram admin alert to {chat_id}: {e}')
    finally:
        await bot.session.close()


async def notify_admins(message: str, dedup_key: str = '', cooldown_seconds: int = 3600) -> None:
    now = time.time()
    if dedup_key and cooldown_seconds > 0:
        last_ts = _last_notified.get(dedup_key, 0.0)
        if (now - last_ts) < cooldown_seconds:
            return
        _last_notified[dedup_key] = now

    if settings.ENABLE_MATRIX_BOT and settings.MATRIX_ADMIN_USERS:
        matrix_msg = message.replace('\n', '<br>')
        for uid in settings.MATRIX_ADMIN_USERS:
            try:
                await _send_matrix_dm(uid, matrix_msg)
            except Exception as e:
                logger.error(f'Matrix admin notify error ({uid}): {e}')

    if settings.ENABLE_TELEGRAM_BOT and settings.TELEGRAM_ADMIN_USERS:
        for tg_id in settings.TELEGRAM_ADMIN_USERS:
            try:
                await _send_telegram_dm(tg_id, message)
            except Exception as e:
                logger.error(f'Telegram admin notify error ({tg_id}): {e}')
