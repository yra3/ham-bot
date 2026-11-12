# -*- coding: utf-8 -*-
from typing import Dict

HAPP_LINKS: Dict[str, Dict[str, str]] = {
    'android': {
        'label': '📱 Телефон (Android)',
        'primary_label': 'Google Play',
        'primary_url': 'https://play.google.com/store/apps/details?id=com.happproxy',
        'secondary_label': 'GitHub (прямой APK)',
        'secondary_url': 'https://github.com/Happ-proxy/happ-android/releases/latest/download/Happ.apk',
    },
    'ios': {
        'label': '🍏 Телефон (iPhone / iPad)',
        'primary_label': 'App Store (RU)',
        'primary_url': 'https://apps.apple.com/ru/app/happ-proxy-utility/id6783623643',
        'secondary_label': 'App Store (US / Global)',
        'secondary_url': 'https://apps.apple.com/us/app/happ-proxy-utility/id6504287215',
    },
    'windows': {
        'label': '💻 Компьютер (Windows)',
        'primary_label': 'GitHub (установщик .exe)',
        'primary_url': 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe',
        'secondary_label': 'Официальный сайт',
        'secondary_url': 'https://www.happ.su/main/ru',
    },
    'macos': {
        'label': '🍎 Компьютер (macOS)',
        'primary_label': 'GitHub (.dmg)',
        'primary_url': 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.macOS.universal.dmg',
        'secondary_label': 'Официальный сайт',
        'secondary_url': 'https://www.happ.su/main/ru',
    },
    'linux': {
        'label': '🐧 Компьютер (Linux)',
        'primary_label': 'GitHub (.deb)',
        'primary_url': 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.linux.x64.deb',
        'secondary_label': 'Все сборки (GitHub)',
        'secondary_url': 'https://github.com/Happ-proxy/happ-desktop/releases/latest',
    },
}

ALT_APPS_BY_OS: Dict[str, str] = {
    'android': (
        '<b>📱 Телефон (Android) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — <a href="https://play.google.com/store/apps/details?id=llc.itdev.incy">Google Play</a> '
        '| <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/Incy.apk">GitHub (APK)</a>\n'
        '• <b>v2RayTun</b> — <a href="https://play.google.com/store/apps/details?id=com.v2raytun.android">Google Play</a> '
        '| <a href="https://t.me/v2raytun/3">Telegram-канал</a>\n'
        '• <b>v2rayNG</b> — <a href="https://github.com/2dust/v2rayNG/releases/latest">GitHub (релизы)</a>\n\n'
        '<i>💡 Совет для Android: если ставите приложения через APK с GitHub, установите '
        '<a href="https://github.com/ImranR98/Obtainium/releases/latest">Obtainium</a> — он умеет автоматически обновлять их прямо с GitHub.</i>'
    ),
    'ios': (
        '<b>🍏 Телефон (iPhone / iPad) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — <a href="https://apps.apple.com/ru/app/incy/id6756943388">App Store</a>\n'
        '• <b>v2RayTun</b> — <a href="https://t.me/v2raytun/3">Официальная группа (ссылки на App Store)</a>'
    ),
    'windows': (
        '<b>💻 Компьютер (Windows) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/incy-windows-setup.exe">GitHub (.exe)</a>\n'
        '• <b>v2rayN</b> — <a href="https://github.com/2dust/v2rayN/releases/latest/download/v2rayN-windows-64-SelfContained.zip">GitHub (.zip)</a>'
    ),
    'macos': (
        '<b>🍎 Компьютер (macOS) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — <a href="https://apps.apple.com/ru/app/incy/id6756943388">App Store</a> '
        '| <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/incy-macos-arm64.dmg">GitHub (Apple Silicon .dmg)</a> '
        '| <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/incy-macos-intel.dmg">GitHub (Intel .dmg)</a>'
    ),
    'linux': (
        '<b>🐧 Компьютер (Linux) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/incy-linux-x64.deb">GitHub (.deb)</a> '
        '| <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest">Все пакеты</a>'
    ),
}

NO_VPN_TOOLS_TEXT = (
    '<b>⚡ Полезные приложения (работа без общего VPN):</b>\n\n'
    '📱 <b>Телефон (Android) — TG WS Proxy</b>\n'
    'Зачем: ускоряет и стабилизирует работу Telegram напрямую, без включения общего VPN.\n'
    'Скачать: <a href="https://github.com/Regstar2/tg-ws-proxy-android/releases/latest">GitHub (последняя версия)</a>\n\n'
    '📱 <b>Телефон (Android) — ByeByeDPI</b>\n'
    'Зачем: помогает открыть YouTube, Discord и другие сервисы без зарубежного VPN (обходит замедление на устройстве).\n'
    'Скачать: <a href="https://github.com/romanvht/ByeByeDPI/releases/latest">GitHub (последняя версия)</a>\n\n'
    '📱 <b>Телефон (Android) — Obtainium</b>\n'
    'Зачем: автоматически проверяет и обновляет приложения, установленные с GitHub (включая Happ, Incy, TG WS Proxy, ByeByeDPI).\n'
    'Скачать: <a href="https://github.com/ImranR98/Obtainium/releases/latest">GitHub (последняя версия)</a>'
)


def build_happ_links_line(os_key: str) -> str:
    info = HAPP_LINKS[os_key]
    return (
        f'{info["label"]}: '
        f'<a href="{info["primary_url"]}">{info["primary_label"]}</a> · '
        f'<a href="{info["secondary_url"]}">{info["secondary_label"]}</a>'
    )


def build_os_guide_html(os_key: str, sub_url: str, show_alts: bool = False) -> str:
    info = HAPP_LINKS[os_key]
    text = (
        f'<b>{info["label"]} — настройка</b>\n\n'
        '⭐ <b>Рекомендуемое приложение: Happ</b>\n'
        f'• Основной способ: <a href="{info["primary_url"]}">{info["primary_label"]}</a>\n'
        f'• Дополнительно: <a href="{info["secondary_url"]}">{info["secondary_label"]}</a>\n\n'
        '<b>Как подключить (3 шага):</b>\n'
        '1. Скачай и установи <b>Happ</b>.\n'
        '2. Скопируй свою ссылку:\n'
        f'<code>{sub_url}</code>\n'
        '3. В приложении нажми <b>«+» ➔ «Добавить из ссылки»</b>, вставь её и нажми <b>«Обновить»</b>.\n\n'
        '<i>Российские сайты (банки, Госуслуги, маркетплейсы) будут открываться напрямую, остальные — через сервер.</i>'
    )
    if show_alts:
        text += '\n\n' + ALT_APPS_BY_OS[os_key]
    return text


def build_matrix_welcome_html(sub_url: str, is_admin: bool = False) -> str:
    happ_list = '<br>'.join(
        build_happ_links_line(k) for k in ('android', 'ios', 'windows', 'macos', 'linux')
    )
    text = (
        '<b>Привет! Я помогу настроить быстрый и стабильный доступ в сеть.</b><br><br>'
        '⭐ <b>Рекомендуемое приложение — Happ</b> (уже с правильными маршрутами для РФ):<br>'
        f'{happ_list}<br><br>'
        '<b>Как подключить за 3 шага:</b><br>'
        '1. Установи <b>Happ</b> на телефон или компьютер по ссылке выше.<br>'
        '2. Скопируй ссылку на готовую подписку:<br>'
        f'<code>{sub_url}</code><br>'
        '3. В приложении нажми <b>«+» ➔ «Добавить из ссылки»</b>, вставь её и нажми <b>«Обновить»</b>.<br>'
        '<i>Банки, Госуслуги и маркетплейсы работают напрямую!</i><br><br>'
        '----------------------------------------<br>'
        '<b>Дополнительно:</b><br>'
        '• <code>!apps</code> — альтернативные программы (Incy, v2RayTun, v2rayN/NG) и утилиты без VPN (TG WS Proxy, ByeByeDPI)<br>'
        '• <code>!happ</code> — напомнить ссылку на подписку<br>'
        '• <code>!vless</code> — список vless ссылок (для опытных)<br>'
        '• <code>!qr</code> — QR-код<br>'
        '• <code>!router</code> — конфиг для роутера<br>'
        '• <code>!all</code> — резервная подписка'
    )
    if is_admin:
        text += (
            '<br><br>----------------------------------------<br>'
            '🔧 <b>Команды администратора:</b><br>'
            '• <code>!admin force_refresh</code> — принудительно обновить ноды с апстрима<br>'
            '• <code>!admin check</code> — экспресс-тест доступности серверов<br>'
            '• <code>!admin status</code> — статус кэша и живых серверов<br>'
            '• <code>!admin tg_invite</code> — одноразовая ссылка-приглашение в Telegram<br>'
            '• <code>!admin tg_users</code> — список пользователей Telegram<br>'
            '• <code>!admin tg_revoke &lt;id&gt;</code> — отозвать доступ пользователю Telegram'
        )
    return text


def build_matrix_apps_html() -> str:
    alts = '<br><br>'.join(
        ALT_APPS_BY_OS[k].replace('\n', '<br>') for k in ('android', 'ios', 'windows', 'macos', 'linux')
    )
    tools = NO_VPN_TOOLS_TEXT.replace('\n', '<br>')
    return (
        '<b>Альтернативные программы</b> (поддерживают ту же ссылку подписки <code>!happ</code>):<br><br>'
        f'{alts}<br><br>'
        '----------------------------------------<br><br>'
        f'{tools}'
    )
