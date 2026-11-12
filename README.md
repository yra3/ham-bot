# ham-bot

Network profile aggregator and endpoint distribution service.

## Documentation

- [Руководство по развёртыванию и настройке (RU)](docs/guides/setup.md)

## Requirements

- Python 3.11+ or Docker
- Docker Compose

## Setup

1. Copy env example:
   ```bash
   cp .env.example .env
   ```

2. Fill required variables (see [docs/guides/setup.md](docs/guides/setup.md)) and run with Docker Compose:
   ```bash
   docker compose up -d --build
   ```

3. Optional local SOCKS5 proxy sidecar (for Telegram API access in restricted networks):
   Set `TELEGRAM_PROXY_URL=socks5://xray:10808` in `.env` and run:
   ```bash
   docker compose --profile proxy up -d --build
   ```

## Development

- Create virtualenv: `python3 -m venv .venv`
- Install deps: `pip install -r requirements.txt`
- Run: `python -m src.main`
