import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from aiogram import BaseMiddleware, Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ChatMemberStatus, ChatType, ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BufferedInputFile,
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    TelegramObject,
)

from src.bot.content import (
    NO_VPN_TOOLS_TEXT,
    build_os_guide_html,
)
from src.config import settings
from src.core import db
from src.core.checker import NodeHealthChecker, check_node
from src.core.fetcher import SubscriptionFetcher
from src.core.parser import ProxyNode, parse_upstream_json
from src.generators.uri import generate_qr_bytes, node_to_vless_uri
from src.generators.xray import generate_router_outbound_json

logger = logging.getLogger('telegram-bot')

fetcher = SubscriptionFetcher(
    sub_url=settings.SUB_URL,
    hwid=settings.HWID,
    cache_ttl_hours=settings.CACHE_TTL_HOURS,
)
checker = NodeHealthChecker(target_alive=settings.TARGET_ALIVE_NODES)


def _format_admin_contacts() -> str:
    contacts = []
    if settings.ADMIN_CONTACT_TG:
        contacts.append(f'• Telegram: <code>{settings.ADMIN_CONTACT_TG}</code>')
    if settings.ADMIN_CONTACT_MATRIX:
        contacts.append(f'• Matrix: <code>{settings.ADMIN_CONTACT_MATRIX}</code>')
    if not contacts:
        return 'Обратитесь к владельцу сервиса за персональной ссылкой.'
    return 'Запросить пригласительную ссылку можно у администратора:\n' + '\n'.join(contacts)


async def send_stranger_notice_once(bot: Bot, user_id: int, chat_id: int) -> None:
    if db.mark_stranger_if_new('tg', str(user_id)):
        text = (
            '🔒 <b>Доступ к боту закрыт и работает только по пригласительной ссылке.</b>\n\n'
            f'{_format_admin_contacts()}'
        )
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.warning(f'Failed to send stranger notice to {user_id}: {e}')


async def get_working_node() -> Optional[ProxyNode]:
    raw_data, _ = await fetcher.fetch()
    nodes = parse_upstream_json(raw_data, whitelist=settings.REGION_WHITELIST)
    if not nodes:
        return None
    for candidate in checker.alive_nodes:
        if await check_node(candidate):
            return candidate
    for node in nodes:
        if await check_node(node):
            if node not in checker.alive_nodes:
                checker.alive_nodes.append(node)
            return node
    return nodes[0]


async def get_working_nodes_list(limit: int = 5) -> List[ProxyNode]:
    raw_data, _ = await fetcher.fetch()
    nodes = parse_upstream_json(raw_data, whitelist=settings.REGION_WHITELIST)
    if not nodes:
        return []
    if checker.alive_nodes and await check_node(checker.alive_nodes[0]):
        return checker.alive_nodes[:limit]
    alive = await checker.scan_pool(nodes, quick=True)
    return (alive or nodes)[:limit]


async def set_personal_commands(bot: Bot, chat_id: int, is_admin: bool) -> None:
    cmds = [
        BotCommand(command='start', description='Главное меню и выбор устройства'),
        BotCommand(command='happ', description='Ссылка-подписка для Happ (рекомендуется)'),
        BotCommand(command='tools', description='Работа без VPN (Telegram, YouTube)'),
        BotCommand(command='qr', description='QR-код для сканирования'),
        BotCommand(command='vless', description='Одна проверенная vless ссылка'),
        BotCommand(command='raw', description='Список vless ссылок'),
        BotCommand(command='router', description='Файл для роутера'),
        BotCommand(command='all', description='Резервная ссылка со всеми серверами'),
    ]
    if is_admin:
        cmds.extend([
            BotCommand(command='invite', description='Создать одноразовый инвайт'),
            BotCommand(command='users', description='Список пользователей'),
            BotCommand(command='status', description='Статус кэша и узлов'),
        ])
    try:
        await bot.set_my_commands(cmds, scope=BotCommandScopeChat(chat_id=chat_id))
    except Exception as e:
        logger.debug(f'Could not set personal commands for {chat_id}: {e}')


def _main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📱 Телефон (Android)', callback_data='os:android'),
            InlineKeyboardButton(text='🍏 Телефон (iPhone)', callback_data='os:ios'),
        ],
        [
            InlineKeyboardButton(text='💻 Компьютер (Windows)', callback_data='os:windows'),
            InlineKeyboardButton(text='🍎 Компьютер (macOS)', callback_data='os:macos'),
        ],
        [
            InlineKeyboardButton(text='🐧 Компьютер (Linux)', callback_data='os:linux'),
            InlineKeyboardButton(text='🌐 Роутер', callback_data='nav:router'),
        ],
        [
            InlineKeyboardButton(text='⚡ Без VPN (Telegram / YouTube)', callback_data='nav:tools'),
        ],
    ])


def _os_keyboard(os_key: str, showing_alts: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if not showing_alts:
        rows.append([InlineKeyboardButton(text='🔄 Альтернативные программы', callback_data=f'alt:{os_key}')])
    else:
        btn_label = '⭐ Основная инструкция (v2RayTun / Happ)' if os_key == 'android' else '⭐ Только Happ (основное)'
        rows.append([InlineKeyboardButton(text=btn_label, callback_data=f'os:{os_key}')])
    rows.append([
        InlineKeyboardButton(text='⚡ Без VPN (TG / YouTube)', callback_data='nav:tools'),
        InlineKeyboardButton(text='◀️ Выбор устройства', callback_data='nav:home'),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _back_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Выбор устройства', callback_data='nav:home')],
    ])


def _help_text(sub_token: str, is_admin: bool) -> str:
    smart_url = settings.build_sub_url(sub_token, 'verified-smart')
    text = (
        '<b>Привет! Я помогу настроить быстрый доступ в сеть.</b>\n\n'
        'Выбери своё устройство кнопкой ниже — я покажу, какое приложение скачать и как его подключить.\n\n'
        '⭐ <b>Рекомендуемое приложение — Happ</b>\n'
        'Твоя персональная ссылка для него:\n'
        f'<code>{smart_url}</code>\n\n'
        '<i>Для опытных: /vless — одна ссылка, /raw — список vless ссылок, /qr — QR-код, /router — роутер.</i>'
    )
    if is_admin:
        text += (
            '\n\n<b>Команды администратора:</b>\n'
            '• /invite — одноразовая пригласительная ссылка\n'
            '• /users — список пользователей\n'
            '• /revoke &lt;id&gt; — отозвать доступ и подписку\n'
            '• /status — статус кэша и серверов\n'
            '• /check — экспресс-проверка серверов\n'
            '• /force_refresh — принудительно обновить подписку с апстрима'
        )
    return text


class AccessControlMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data['bot']

        if isinstance(event, CallbackQuery):
            user = event.from_user
            msg = event.message
            if not user or user.is_bot or not msg:
                return
            uid = user.id
            is_admin = uid in settings.TELEGRAM_ADMIN_USERS
            chat_type = msg.chat.type
            if chat_type == ChatType.PRIVATE:
                if is_admin or db.is_tg_user_allowed(uid):
                    return await handler(event, data)
                await event.answer('Доступ только по приглашению.', show_alert=True)
                return
            if chat_type in (ChatType.GROUP, ChatType.SUPERGROUP):
                if db.is_group_allowed(msg.chat.id) and (is_admin or db.is_tg_user_allowed(uid)):
                    return await handler(event, data)
                return
            return

        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user or user.is_bot:
            return

        uid = user.id
        is_admin = uid in settings.TELEGRAM_ADMIN_USERS
        chat_type = event.chat.type

        if chat_type == ChatType.PRIVATE:
            if is_admin or db.is_tg_user_allowed(uid):
                return await handler(event, data)

            text = (event.text or '').strip()
            if text.startswith('/start ') and len(text.split(maxsplit=1)) == 2:
                return await handler(event, data)

            await send_stranger_notice_once(bot, uid, event.chat.id)
            return

        if chat_type in (ChatType.GROUP, ChatType.SUPERGROUP):
            if not db.is_group_allowed(event.chat.id):
                return
            if is_admin or db.is_tg_user_allowed(uid):
                return await handler(event, data)
            return


router = Router()


@router.my_chat_member()
async def on_my_chat_member(event: ChatMemberUpdated, bot: Bot) -> None:
    chat = event.chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    new_status = event.new_chat_member.status
    actor_id = event.from_user.id

    if new_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
        admin_present = actor_id in settings.TELEGRAM_ADMIN_USERS
        if not admin_present:
            try:
                admins = await bot.get_chat_administrators(chat.id)
                admin_present = any(a.user.id in settings.TELEGRAM_ADMIN_USERS for a in admins)
            except Exception as e:
                logger.warning(f'Could not inspect chat admins for {chat.id}: {e}')

        if admin_present:
            db.set_group_allowed(chat.id, chat.title or '', actor_id, active=True)
            logger.info(f'Authorized group {chat.id} ({chat.title}) added by admin {actor_id}')
        else:
            db.set_group_allowed(chat.id, chat.title or '', actor_id, active=False)
            logger.warning(f'Unauthorized group add {chat.id} ({chat.title}) by {actor_id}; leaving.')
            try:
                await bot.leave_chat(chat.id)
            except Exception as e:
                logger.error(f'Failed to leave unauthorized group {chat.id}: {e}')
    elif new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
        db.set_group_allowed(chat.id, chat.title or '', actor_id, active=False)


@router.chat_member()
async def on_chat_member(event: ChatMemberUpdated, bot: Bot) -> None:
    chat = event.chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return
    if not db.is_group_allowed(chat.id):
        return

    target_id = event.new_chat_member.user.id
    if target_id not in settings.TELEGRAM_ADMIN_USERS:
        return

    if event.new_chat_member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
        try:
            admins = await bot.get_chat_administrators(chat.id)
            if not any(a.user.id in settings.TELEGRAM_ADMIN_USERS for a in admins):
                db.set_group_allowed(chat.id, chat.title or '', target_id, active=False)
                await bot.leave_chat(chat.id)
                logger.info(f'Admin left group {chat.id}; bot leaving too.')
        except Exception as e:
            logger.warning(f'Failed checking admins after leave in {chat.id}: {e}')


def _get_user_token_from_user(u) -> str:
    return db.get_or_create_tg_user(
        user_id=u.id,
        username=u.username or '',
        full_name=u.full_name or '',
    )


@router.message(Command('start'))
async def cmd_start(message: Message, command: CommandObject, bot: Bot) -> None:
    u = message.from_user
    is_admin = u.id in settings.TELEGRAM_ADMIN_USERS
    already_allowed = is_admin or db.is_tg_user_allowed(u.id)

    if not already_allowed:
        code = (command.args or '').strip()
        if not code:
            await send_stranger_notice_once(bot, u.id, message.chat.id)
            return

        sub_token = db.redeem_invite(
            code=code,
            user_id=u.id,
            username=u.username or '',
            full_name=u.full_name or '',
        )
        if not sub_token:
            await send_stranger_notice_once(bot, u.id, message.chat.id)
            return

        logger.info(f'User {u.id} (@{u.username}) redeemed invite {code}')
        for admin_id in settings.TELEGRAM_ADMIN_USERS:
            try:
                uname = f'@{u.username}' if u.username else u.full_name
                await bot.send_message(
                    admin_id,
                    f'✅ Новый пользователь активировал инвайт: {uname} (ID: <code>{u.id}</code>)',
                )
            except Exception:
                pass
    else:
        sub_token = _get_user_token_from_user(u)

    await set_personal_commands(bot, message.chat.id, is_admin)
    await message.answer(
        _help_text(sub_token, is_admin),
        reply_markup=_main_menu_keyboard(),
        disable_web_page_preview=True,
    )


@router.message(Command('help'))
async def cmd_help(message: Message) -> None:
    is_admin = message.from_user.id in settings.TELEGRAM_ADMIN_USERS
    sub_token = _get_user_token_from_user(message.from_user)
    await message.answer(
        _help_text(sub_token, is_admin),
        reply_markup=_main_menu_keyboard(),
        disable_web_page_preview=True,
    )


@router.message(Command('tools'))
async def cmd_tools(message: Message) -> None:
    await message.answer(
        NO_VPN_TOOLS_TEXT,
        reply_markup=_back_home_keyboard(),
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith('os:'))
async def cb_os_select(callback: CallbackQuery) -> None:
    os_key = callback.data.split(':', 1)[1]
    sub_token = _get_user_token_from_user(callback.from_user)
    smart_url = settings.build_sub_url(sub_token, 'verified-smart')
    await callback.message.edit_text(
        build_os_guide_html(os_key, smart_url, show_alts=False),
        reply_markup=_os_keyboard(os_key, showing_alts=False),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith('alt:'))
async def cb_os_alts(callback: CallbackQuery) -> None:
    os_key = callback.data.split(':', 1)[1]
    sub_token = _get_user_token_from_user(callback.from_user)
    smart_url = settings.build_sub_url(sub_token, 'verified-smart')
    await callback.message.edit_text(
        build_os_guide_html(os_key, smart_url, show_alts=True),
        reply_markup=_os_keyboard(os_key, showing_alts=True),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == 'nav:home')
async def cb_home(callback: CallbackQuery) -> None:
    is_admin = callback.from_user.id in settings.TELEGRAM_ADMIN_USERS
    sub_token = _get_user_token_from_user(callback.from_user)
    await callback.message.edit_text(
        _help_text(sub_token, is_admin),
        reply_markup=_main_menu_keyboard(),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == 'nav:tools')
async def cb_tools(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        NO_VPN_TOOLS_TEXT,
        reply_markup=_back_home_keyboard(),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == 'nav:router')
async def cb_router(callback: CallbackQuery) -> None:
    await callback.answer('Готовлю файл для роутера...')
    node = await get_working_node()
    if not node:
        await callback.message.answer('⚠️ Нет доступных серверов.')
        return
    outbound_json = generate_router_outbound_json(node)
    json_bytes = json.dumps(outbound_json, indent=2, ensure_ascii=False).encode('utf-8')
    doc = BufferedInputFile(json_bytes, filename='proxy-outbound.json')
    await callback.message.answer_document(document=doc, caption=f'🌐 <b>Конфигурация для роутера:</b> {node.remarks}')


@router.message(Command('happ'))
async def cmd_happ(message: Message) -> None:
    sub_token = _get_user_token_from_user(message.from_user)
    smart_url = settings.build_sub_url(sub_token, 'verified-smart')
    await message.answer(
        '⭐ <b>Рекомендуемое приложение — Happ</b>\n\n'
        'Персональная ссылка-подписка:\n'
        f'<code>{smart_url}</code>\n\n'
        '1. Скопируй ссылку выше.\n'
        '2. В приложении <b>Happ</b> нажми <b>«+» ➔ «Добавить из ссылки»</b>.\n'
        '3. Вставь и нажми <b>«Обновить»</b>.',
        reply_markup=_main_menu_keyboard(),
        disable_web_page_preview=True,
    )


@router.message(Command('all'))
async def cmd_all(message: Message) -> None:
    sub_token = _get_user_token_from_user(message.from_user)
    all_url = settings.build_sub_url(sub_token, 'all-smart')
    await message.answer(
        '🌐 <b>Резервная ссылка со всеми серверами:</b>\n\n'
        f'<code>{all_url}</code>'
    )


@router.message(Command('vless'))
async def cmd_vless(message: Message) -> None:
    node = await get_working_node()
    if not node:
        await message.answer('⚠️ Нет доступных серверов.')
        return
    uri = node_to_vless_uri(node)
    await message.answer(
        '🔗 <b>Прямая ссылка на проверенный сервер:</b>\n'
        f'📍 <b>Локация:</b> {node.remarks}\n\n'
        f'<code>{uri}</code>'
    )


@router.message(Command('raw'))
async def cmd_raw(message: Message) -> None:
    working = await get_working_nodes_list(limit=5)
    if not working:
        await message.answer('⚠️ Нет доступных серверов.')
        return
    lines = [f'• {n.remarks}\n<code>{node_to_vless_uri(n)}</code>' for n in working]
    await message.answer('🔗 <b>Список vless ссылок:</b>\n\n' + '\n\n'.join(lines))


@router.message(Command('qr'))
async def cmd_qr(message: Message) -> None:
    node = await get_working_node()
    if not node:
        await message.answer('⚠️ Нет доступных серверов.')
        return
    uri = node_to_vless_uri(node)
    qr_bytes = generate_qr_bytes(uri)
    photo = BufferedInputFile(qr_bytes, filename='qr.png')
    await message.answer_photo(photo=photo, caption=f'📸 <b>{node.remarks}</b>')


@router.message(Command('router'))
async def cmd_router(message: Message) -> None:
    node = await get_working_node()
    if not node:
        await message.answer('⚠️ Нет доступных серверов.')
        return
    outbound_json = generate_router_outbound_json(node)
    json_bytes = json.dumps(outbound_json, indent=2, ensure_ascii=False).encode('utf-8')
    doc = BufferedInputFile(json_bytes, filename='proxy-outbound.json')
    await message.answer_document(document=doc, caption=f'🌐 <b>Конфигурация для роутера:</b> {node.remarks}')


@router.message(Command('invite'))
async def cmd_invite(message: Message, bot: Bot) -> None:
    if message.from_user.id not in settings.TELEGRAM_ADMIN_USERS:
        return
    code = db.create_invite(created_by=f'tg:{message.from_user.id}', ttl_hours=24)
    me = await bot.get_me()
    db.set_meta('tg_bot_username', me.username or '')
    link = f'https://t.me/{me.username}?start={code}'
    await message.answer(
        '🎟️ <b>Одноразовая пригласительная ссылка (действует 24ч):</b>\n\n'
        f'<code>{link}</code>'
    )


@router.message(Command('users'))
async def cmd_users(message: Message) -> None:
    if message.from_user.id not in settings.TELEGRAM_ADMIN_USERS:
        return
    users = db.list_tg_users()
    if not users:
        await message.answer('📭 Пользователей пока нет.')
        return
    lines = []
    for u in users:
        st = '✅' if u['is_active'] else '🚫'
        uname = f"@{u['username']}" if u['username'] else u['full_name'] or 'без имени'
        lines.append(f"{st} <code>{u['user_id']}</code> ({uname})")
    await message.answer('👥 <b>Пользователи Telegram:</b>\n' + '\n'.join(lines))


@router.message(Command('revoke'))
async def cmd_revoke(message: Message, command: CommandObject) -> None:
    if message.from_user.id not in settings.TELEGRAM_ADMIN_USERS:
        return
    arg = (command.args or '').strip()
    if not arg.isdigit():
        await message.answer('Укажите числовой ID: <code>/revoke 123456789</code>')
        return
    ok = db.revoke_tg_user(int(arg))
    if ok:
        await message.answer(f'🚫 Доступ и подписка пользователя <code>{arg}</code> отозваны.')
    else:
        await message.answer(f'Пользователь <code>{arg}</code> не найден.')


@router.message(Command('status'))
async def cmd_status(message: Message) -> None:
    if message.from_user.id not in settings.TELEGRAM_ADMIN_USERS:
        return
    is_valid = fetcher.is_cache_valid()
    alive_cnt = len(checker.alive_nodes)
    is_act = 'Актуален ✅' if is_valid else 'Устарел / отсутствует ⚠️'
    await message.answer(
        '📊 <b>Диагностика системы:</b>\n'
        f'• Кэш подписки: {is_act}\n'
        f'• Живых серверов в памяти: <b>{alive_cnt}</b>\n'
        f'• Лимит (TARGET_ALIVE_NODES): <b>{settings.TARGET_ALIVE_NODES}</b>\n'
        f'• Регионы: <code>{", ".join(settings.REGION_WHITELIST)}</code>'
    )


@router.message(Command('check'))
async def cmd_check(message: Message) -> None:
    if message.from_user.id not in settings.TELEGRAM_ADMIN_USERS:
        return
    await message.answer('🔍 Запускаю проверку доступности узлов...')
    raw_data, _ = await fetcher.fetch()
    nodes = parse_upstream_json(raw_data, whitelist=settings.REGION_WHITELIST)
    alive = await checker.scan_pool(nodes, quick=True)
    alive_list = '\n'.join([f'• {n.remarks} ({n.address}:{n.port})' for n in alive])
    await message.answer(f'✅ Проверка завершена ({len(alive)}/{len(nodes)}):\n{alive_list}')


@router.message(Command('force_refresh'))
async def cmd_force_refresh(message: Message) -> None:
    if message.from_user.id not in settings.TELEGRAM_ADMIN_USERS:
        return
    from src.generators.xray import sync_sidecar_xray_config
    await message.answer('⏳ Обновляю подписку с апстрима...')
    data, _ = await fetcher.fetch(force=True)
    nodes = parse_upstream_json(data, whitelist=settings.REGION_WHITELIST)
    checker.alive_nodes = []
    alive = await checker.scan_pool(nodes, quick=True)
    await sync_sidecar_xray_config(fetcher, checker, settings.REGION_WHITELIST)
    await message.answer(f'✅ Готово! Валидных нод: {len(nodes)}, живых: {len(alive)}.')


class TelegramBotService:
    async def start(self) -> None:
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.error('TELEGRAM_BOT_TOKEN is empty. Skipping Telegram bot.')
            return

        session = AiohttpSession(proxy=settings.TELEGRAM_PROXY_URL) if settings.TELEGRAM_PROXY_URL else None
        bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher()
        mw = AccessControlMiddleware()
        dp.message.middleware(mw)
        dp.callback_query.middleware(mw)
        dp.include_router(router)

        try:
            me = None
            for attempt in range(1, 11):
                try:
                    me = await bot.get_me()
                    break
                except Exception as e:
                    logger.warning(f'Telegram API connect attempt {attempt}/10 failed ({e}); retrying in 3s...')
                    await asyncio.sleep(3)

            if not me:
                logger.error('Telegram bot could not connect to API after 10 attempts.')
                return

            db.set_meta('tg_bot_username', me.username or '')
            # Keep global commands empty so strangers don't see bot commands
            await bot.set_my_commands([])
            logger.info(f'Starting Telegram bot polling as @{me.username}...')
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        except Exception as e:
            logger.error(f'Telegram bot failed to start/poll: {e}')
        finally:
            await bot.session.close()
