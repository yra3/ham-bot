# Руководство по развёртыванию и настройке

## 1. Предварительные требования

- Docker и Docker Compose
- Обратный прокси (Caddy / Nginx), направляющий домен `SUB_DOMAIN` на порт хоста `HOST_PORT` (по умолчанию `8088`), **или** прямой доступ по IP и порту `http://<IP>:8088` без обратного прокси

## 2. Настройка `.env`: что нужно указать обязательно, а что можно не менять

Скопируйте пример конфигурации:

```bash
cp .env.example .env
```

### Обязательно заполнить

#### А. Без этих параметров приложение не запустится (нет значений по умолчанию)

- `SUB_URL` — URL апстрим-подписки.
- `HWID` — идентификатор устройства/оборудования (передаётся в заголовке `X-HWID`).
- `SUB_SECRET_TOKEN` — главный секретный токен для ссылок подписки (сгенерируйте через `openssl rand -hex 16`).

#### Б. Нужно заменить на свои значения для реальной работы

- **Адрес раздатчика подписок** (выберите один из вариантов):
  - **Если есть домен с HTTPS** (через Caddy/Nginx): укажите `SUB_DOMAIN=sub.example.com` (без `https://`).
  - **Если домена нет, а есть только IP (или нужен HTTP / нестандартный порт):** укажите `SUB_BASE_URL=http://203.0.113.10:8088` (если `SUB_BASE_URL` задан, он перекрывает `SUB_SCHEME` и `SUB_DOMAIN`).
- Переключатели платформ (по умолчанию в коде включён только Matrix):
  - `ENABLE_MATRIX_BOT` (`true` / `false`)
  - `ENABLE_TELEGRAM_BOT` (`true` / `false`)
- Если включён Telegram-бот (`ENABLE_TELEGRAM_BOT=true`):
  - `TELEGRAM_BOT_TOKEN` — токен от `@BotFather`.
  - `TELEGRAM_ADMIN_USERS` — JSON-список числовых ID администраторов, например `[123456789]`.
- Если включён Matrix-бот (`ENABLE_MATRIX_BOT=true`):
  - `MATRIX_HOMESERVER` — адрес вашего Matrix-сервера, например `https://matrix.example.com`.
  - `MATRIX_USER_ID` — Matrix ID бота, например `@ham-bot:example.com`.
  - `MATRIX_ACCESS_TOKEN` — токен доступа бота.
  - `MATRIX_ADMIN_USERS` — JSON-список Matrix ID администраторов, например `["@admin:example.com"]`.

### Можно не трогать (уже есть значения по умолчанию)

Эти параметры можно оставить как есть в `.env.example` или не указывать в `.env`:

- `SUB_BASE_URL` — `""` (пусто; если заполнен, например `http://203.0.113.10:8088`, используется вместо `SUB_SCHEME` + `SUB_DOMAIN`).
- `SUB_SCHEME` — `https` (схема для `SUB_DOMAIN`, можно переключить на `http`).
- `SUB_DOMAIN` — `sub.example.com` (домен без схемы, используется если пуст `SUB_BASE_URL`).
- `HOST_PORT` — `8088` (внешний порт на хосте в `docker-compose.yml`, на котором слушает раздатчик).
- `PORT` — `8080` (порт веб-сервера внутри контейнера).
- `CACHE_TTL_HOURS` — `24` (время жизни кэша апстрима в часах).
- `CHECK_SCHEDULE_CRON` — `0 1 * * *`.
- `TARGET_ALIVE_NODES` — `5` (сколько рабочих нод отбирать; `-1` — проверять все).
- `REGION_WHITELIST` — `["Финляндия", "Нидерланды"]` (`[]` отключает фильтрацию по регионам).
- `DIRECT_DOMAINS` — `[]` (JSON-список доменов, которые всегда идут напрямую в обход прокси, например `["example.com", "chat.example.com"]`).
- `ENABLE_MATRIX_BOT` — `true`.
- `ENABLE_TELEGRAM_BOT` — `false`.
- `TELEGRAM_PROXY_URL` — `""` (пусто; нужно только при запуске с профилем `proxy` → `socks5://xray:10808`).
- `PROXY_BIND_HOST` — `127.0.0.1` (используется в `docker-compose.yml` для SOCKS5-порта sidecar-контейнера `xray`, по умолчанию слушает только localhost).
- `ADMIN_CONTACT_TG` — `""` (опциональный Telegram-контакт, один раз показывается неприглашённым пользователям).
- `ADMIN_CONTACT_MATRIX` — `""` (опциональный Matrix-контакт, один раз показывается неприглашённым пользователям).

## 3. Настройка Telegram-бота

1. Откройте `@BotFather` в Telegram, выполните `/newbot` и сохраните выданный токен в `TELEGRAM_BOT_TOKEN`.
2. Узнайте свой числовой Telegram User ID:
   - Откройте `@userinfobot` в Telegram и отправьте `/start` (или любое сообщение).
   - Скопируйте числовое значение `Id` (например, `123456789`) в `TELEGRAM_ADMIN_USERS=[123456789]`.
3. Установите `ENABLE_TELEGRAM_BOT=true` (и `ENABLE_MATRIX_BOT=false`, если Matrix-бот не нужен).
4. При желании укажите контакты администратора для неприглашённых пользователей:
   - `ADMIN_CONTACT_TG=@your_username`
   - `ADMIN_CONTACT_MATRIX=@admin:example.com`

### Контроль доступа в Telegram

- Личные чаты работают только по приглашениям. Админы генерируют одноразовые инвайты командой `/invite` (или `!admin tg_invite` в Matrix).
- Неприглашённые пользователи получают одно уведомление с контактами админа; последующие сообщения игнорируются.
- Групповые чаты остаются активными только пока в группе присутствует хотя бы один админ из `TELEGRAM_ADMIN_USERS`.

## 4. Настройка Matrix-бота

1. Создайте учётную запись бота на вашем Matrix-сервере и получите `access_token`.
2. Заполните в `.env`:
   - `ENABLE_MATRIX_BOT=true`
   - `MATRIX_HOMESERVER=https://matrix.example.com`
   - `MATRIX_USER_ID=@ham-bot:example.com`
   - `MATRIX_ACCESS_TOKEN=...`
   - `MATRIX_ADMIN_USERS=["@admin:example.com"]`
3. Опционально для аватара профиля: положите файл `assets/avatar.jpg` и перезапустите контейнер.

## 5. Запуск сервиса

Обычный режим:

```bash
docker compose up -d --build
```

С опциональным локальным SOCKS5-прокси (`xray` sidecar, для доступа к Telegram API в заблокированных сетях):

1. Пропишите `TELEGRAM_PROXY_URL=socks5://xray:10808` в `.env`.
2. Оставьте `PROXY_BIND_HOST=127.0.0.1` (значение по умолчанию, только localhost) или укажите IP bridge-интерфейса при необходимости.
3. Конфиг для sidecar (`./data/xray/config.json`) сервис сгенерирует автоматически на основе рабочих нод; при первом запуске может потребоваться перезапуск контейнера `xray` после генерации конфига.
4. Запустите с профилем `proxy`:

```bash
docker compose --profile proxy up -d --build
```
