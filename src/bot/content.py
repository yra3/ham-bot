# -*- coding: utf-8 -*-
from typing import Dict

TG_WS_APK_URL = (
    'https://github.com/Regstar2/tg-ws-proxy-android/releases/download/'
    'v1.11.7/TgWsProxy-Android-v1.11.7-arm64-v8a.apk'
)
BYEBYEDPI_APK_URL = (
    'https://github.com/romanvht/ByeByeDPI/releases/download/'
    'v.1.8.2/ByeByeDPI-v1.8.2-universal-release.apk'
)
OBTAINIUM_APK_URL = (
    'https://github.com/ImranR98/Obtainium/releases/latest/download/'
    'app-arm64-v8a-release.apk'
)

HAPP_LINKS: Dict[str, Dict[str, str]] = {
    'android': {
        'label': '📱 Телефон (Android)',
        'primary_label': 'v2RayTun (Google Play)',
        'primary_url': 'https://play.google.com/store/apps/details?id=com.v2raytun.android',
        'secondary_label': 'Happ (GitHub APK)',
        'secondary_url': 'https://github.com/Happ-proxy/happ-android/releases/latest/download/Happ.apk',
        'secondary_prefix': '(если хотите Happ — вставить ссылку в браузер, скачать и установить файл): ',
    },
    'ios': {
        'label': '🍏 Телефон (iPhone / iPad)',
        'primary_label': 'App Store (RU)',
        'primary_url': 'https://apps.apple.com/ru/app/happ-proxy-utility/id6783623643',
        'secondary_label': 'App Store (US / Global)',
        'secondary_url': 'https://apps.apple.com/us/app/happ-proxy-utility/id6504287215',
        'secondary_prefix': '',
    },
    'windows': {
        'label': '💻 Компьютер (Windows)',
        'primary_label': 'Установщик (.exe)',
        'primary_url': 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe',
        'secondary_label': 'Официальный сайт',
        'secondary_url': 'https://www.happ.su/main/ru',
        'secondary_prefix': '',
    },
    'macos': {
        'label': '🍎 Компьютер (macOS)',
        'primary_label': 'Образ (.dmg)',
        'primary_url': 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.macOS.universal.dmg',
        'secondary_label': 'Официальный сайт',
        'secondary_url': 'https://www.happ.su/main/ru',
        'secondary_prefix': '',
    },
    'linux': {
        'label': '🐧 Компьютер (Linux)',
        'primary_label': 'Пакет (.deb)',
        'primary_url': 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.linux.x64.deb',
        'secondary_label': 'Все сборки (GitHub)',
        'secondary_url': 'https://github.com/Happ-proxy/happ-desktop/releases/latest',
        'secondary_prefix': '',
    },
}

ALT_APPS_BY_OS: Dict[str, str] = {
    'android': (
        '<b>📱 Телефон (Android) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — Скачать: <a href="https://play.google.com/store/apps/details?id=llc.itdev.incy">Google Play</a> '
        '<b>|</b> (если не доступен в Play Store — скачать, вставив ссылку в браузер, и установить файл): '
        '<a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/Incy.apk">GitHub (APK)</a>\n'
        '• <b>v2RayTun</b> — <a href="https://t.me/v2raytun/3">Telegram-канал (резерв)</a>\n'
        '• <b>v2rayNG</b> — Скачать (вставить ссылку в браузер и установить файл): '
        '<a href="https://github.com/2dust/v2rayNG/releases/latest">GitHub (релизы)</a>\n\n'
        '<i>💡 Для автообновления APK с GitHub можно поставить '
        f'<a href="{OBTAINIUM_APK_URL}">Obtainium</a> (вставить ссылку в браузер, скачать и установить файл).</i>'
    ),
    'ios': (
        '<b>🍏 Телефон (iPhone / iPad) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — Скачать: <a href="https://apps.apple.com/ru/app/incy/id6756943388">App Store</a>\n'
        '• <b>v2RayTun</b> — <a href="https://t.me/v2raytun/3">Официальная группа (ссылки на App Store)</a>'
    ),
    'windows': (
        '<b>💻 Компьютер (Windows) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — Скачать: <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/incy-windows-setup.exe">Установщик (.exe)</a>\n'
        '• <b>v2rayN</b> — Скачать: <a href="https://github.com/2dust/v2rayN/releases/latest/download/v2rayN-windows-64-SelfContained.zip">Архив (.zip)</a>'
    ),
    'macos': (
        '<b>🍎 Компьютер (macOS) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — Скачать: <a href="https://apps.apple.com/ru/app/incy/id6756943388">App Store</a> '
        '<b>|</b> <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/incy-macos-arm64.dmg">Apple Silicon (.dmg)</a> '
        '<b>|</b> <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/incy-macos-intel.dmg">Intel (.dmg)</a>'
    ),
    'linux': (
        '<b>🐧 Компьютер (Linux) — альтернативные клиенты:</b>\n'
        '• <b>Incy</b> — Скачать: <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest/download/incy-linux-x64.deb">Пакет (.deb)</a> '
        '<b>|</b> <a href="https://github.com/INCY-DEV/incy-platforms/releases/latest">Все пакеты</a>'
    ),
}

NO_VPN_TG_BLOCK = (
    '<b>Подключить Телеграм без ВПНа</b> 📱 Android\n'
    f'Сначала скачать (вставив ссылку в браузер) и установить файл: <a href="{TG_WS_APK_URL}">TgWsProxy APK</a> ➔ жмём «старт прокси» ➔ жмём «применить в телеграм» ➔ в телеграме жмём ок'
)

NO_VPN_YT_BLOCK = (
    '<b>Смотреть Ютуб без ВПН</b> 📱 Android\n'
    f'Скачать (вставив ссылку в браузер) и установить файл: <a href="{BYEBYEDPI_APK_URL}">ByeByeDPI APK</a> ➔ включить 👍\n'
    '<i>ВПН в этот момент отключается, но Ютуб работает быстрее)</i>'
)

NO_VPN_TOOLS_TEXT = (
    f'{NO_VPN_TG_BLOCK}\n\n'
    f'{NO_VPN_YT_BLOCK}\n\n'
    '<b>📱 Телефон Android — Obtainium (дополнительно)</b>\n'
    'Зачем: автоматически обновляет приложения, скачанные с GitHub.\n'
    f'Скачать (вставив ссылку в браузер) и установить файл: <a href="{OBTAINIUM_APK_URL}">Obtainium APK</a>'
)


def build_happ_links_line(os_key: str) -> str:
    info = HAPP_LINKS[os_key]
    sec_pref = info.get('secondary_prefix', '')
    return (
        f'{info["label"]} — Скачать: '
        f'<a href="{info["primary_url"]}">{info["primary_label"]}</a> <b>|</b> '
        f'{sec_pref}<a href="{info["secondary_url"]}">{info["secondary_label"]}</a>'
    )


def build_os_guide_html(os_key: str, sub_url: str, show_alts: bool = False) -> str:
    info = HAPP_LINKS[os_key]
    if os_key == 'android':
        text = (
            f'<b>{info["label"]} — настройка</b>\n\n'
            '⭐ <b>Рекомендуемое приложение для Google Play: v2RayTun</b> (Happ сейчас удалён из Play Store в РФ)\n'
            f'• Основной способ: Скачать в <a href="{info["primary_url"]}">Google Play</a>\n\n'
            '<b>Как подключить v2RayTun (3 шага):</b>\n'
            '1. Скачай и установи <b>v2RayTun</b> из Google Play.\n'
            '2. Скопируй свою ссылку:\n'
            f'<code>{sub_url}</code>\n'
            '3. В <b>v2RayTun</b> нажми <b>«+»</b> в правом верхнем углу ➔ <b>«Импорт из буфера обмена»</b>, затем выбери сервер и нажми кнопку подключения.\n\n'
            '<b>Если нужен Happ (без Google Play):</b>\n'
            f'• <a href="{info["secondary_url"]}">Happ APK (GitHub)</a> — нужно скачать (вставив ссылку в браузер) и установить файл.\n'
            '• В Happ: нажми <b>«+» ➔ «Добавить из ссылки»</b>, вставь ссылку и нажми <b>«Обновить»</b>.'
        )
    else:
        sec_pref = info.get('secondary_prefix', '')
        github_hint = ' (вставить ссылку в браузер, скачать и установить файл)' if 'github.com' in info['primary_url'] else ''
        text = (
            f'<b>{info["label"]} — настройка</b>\n\n'
            '⭐ <b>Рекомендуемое приложение: Happ</b>\n'
            f'• Основной способ — Скачать: <a href="{info["primary_url"]}">{info["primary_label"]}</a>{github_hint}\n'
            f'• Дополнительно {sec_pref}— Скачать: <a href="{info["secondary_url"]}">{info["secondary_label"]}</a>\n\n'
            '<b>Как подключить (3 шага):</b>\n'
            '1. Скачай и установи <b>Happ</b>.\n'
            '2. Скопируй свою ссылку:\n'
            f'<code>{sub_url}</code>\n'
            '3. В приложении нажми <b>«+» ➔ «Добавить из ссылки»</b>, вставь её и нажми <b>«Обновить»</b>.'
        )
    if show_alts:
        text += '\n\n' + ALT_APPS_BY_OS[os_key]
    return text


def build_matrix_welcome_html(sub_url: str, is_admin: bool = False) -> str:
    happ_list = '<br>'.join(
        build_happ_links_line(k) for k in ('android', 'ios', 'windows', 'macos', 'linux')
    )
    tg_no_vpn_html = NO_VPN_TG_BLOCK.replace('\n', '<br>')
    text = (
        '<b>Привет! Я помогу настроить быстрый и стабильный доступ в сеть.</b><br><br>'
        '⭐ <b>Рекомендуемое приложение — Happ</b> (для Android через Google Play сейчас используйте <b>v2RayTun</b>):<br>'
        f'{happ_list}<br><br>'
        '<b>Как подключить за 3 шага:</b><br>'
        '1. Скачай и установи приложение по ссылке выше.<br>'
        '2. Скопируй ссылку на готовую подписку:<br>'
        f'<code>{sub_url}</code><br>'
        '3. В приложении нажми <b>«+»</b> ➔ <b>«Импорт из буфера обмена»</b> (в v2RayTun) или <b>«Добавить из ссылки»</b> (в Happ), вставь её и обнови.<br><br>'
        '----------------------------------------<br>'
        f'{tg_no_vpn_html}<br><br>'
        '----------------------------------------<br>'
        '<b>Дополнительно:</b><br>'
        '• <code>!apps</code> — ссылки для скачивания других приложений (Incy, v2RayTun, v2rayN/NG, Ютуб без ВПН)<br>'
        '• <code>!happ</code> — напомнить ссылку на подписку<br>'
        '• <code>!vless</code> — одна проверенная vless ссылка<br>'
        '• <code>!raw</code> — список vless ссылок<br>'
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
    yt_html = NO_VPN_YT_BLOCK.replace('\n', '<br>')
    return (
        '<b>Ссылки для скачивания других приложений</b> (поддерживают ту же ссылку подписки <code>!happ</code>):<br><br>'
        f'{alts}<br><br>'
        '----------------------------------------<br><br>'
        f'{yt_html}'
    )
