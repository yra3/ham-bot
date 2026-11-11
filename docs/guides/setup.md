# Deployment and Configuration Guide

## 1. Prerequisites

- Docker & Docker Compose
- Reverse proxy (Caddy / Nginx) pointing `SUB_DOMAIN` to host port `8088`

## 2. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### Core Settings

- `SUB_URL`: Upstream subscription endpoint URL.
- `HWID`: Device/hardware identifier sent in `X-HWID` header.
- `SUB_DOMAIN`: Public domain where your endpoints are served (without `https://`).
- `SUB_SECRET_TOKEN`: Master secret token (`openssl rand -hex 16`).
- `CACHE_TTL_HOURS`: Upstream cache lifetime in hours (default `24`).
- `TARGET_ALIVE_NODES`: Number of verified endpoints to collect (`5` by default, `-1` to check all).
- `REGION_WHITELIST`: JSON list of allowed region substrings, e.g. `["Финляндия", "Нидерланды"]` (empty `[]` disables filtering).
- `DIRECT_DOMAINS`: JSON list of domains that should always be routed directly (`direct`), e.g. `["example.com", "chat.example.com"]`.

## 3. Telegram Bot Setup

1. Open `@BotFather` in Telegram, run `/newbot`, and save the token into `TELEGRAM_BOT_TOKEN`.
2. Get your numeric Telegram User ID:
   - Open `@userinfobot` in Telegram and send `/start` (or any message).
   - Copy the numeric `Id` (e.g., `123456789`) into `TELEGRAM_ADMIN_USERS=[123456789]`.
3. Set `ENABLE_TELEGRAM_BOT=true`.
4. Optional contact shown once to uninvited users:
   - `ADMIN_CONTACT_TG=@your_username`
   - `ADMIN_CONTACT_MATRIX=@admin:example.com`

### Access Control in Telegram

- Private chats are invite-only. Admins generate one-time invites with `/invite` (or `!admin tg_invite` in Matrix).
- Uninvited users receive a single notice with admin contact details; subsequent messages are ignored.
- Group chats remain active only while at least one admin from `TELEGRAM_ADMIN_USERS` is present in the group.

## 4. Matrix Bot Setup

1. Create a bot user on your Matrix homeserver and obtain an `access_token`.
2. Fill in `.env`:
   - `ENABLE_MATRIX_BOT=true`
   - `MATRIX_HOMESERVER=https://matrix.example.com`
   - `MATRIX_USER_ID=@ham-bot:example.com`
   - `MATRIX_ACCESS_TOKEN=...`
   - `MATRIX_ADMIN_USERS=["@admin:example.com"]`
3. Optional profile avatar: place `assets/avatar.jpg` and restart the container.

## 5. Running the Service

Standard mode:

```bash
docker compose up -d --build
```

With optional local SOCKS5 sidecar (`xray` profile):

1. Set `TELEGRAM_PROXY_URL=socks5://xray:10808` in `.env`.
2. Keep `PROXY_BIND_HOST=127.0.0.1` (default, localhost only) or set a bridge IP if needed.
3. Start with the `proxy` profile:

```bash
docker compose --profile proxy up -d --build
```
