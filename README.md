# ham-bot

Network profile aggregator and endpoint distribution service.

## Requirements

- Python 3.11+ or Docker
- Docker Compose

## Setup

1. Copy env example:
   cp .env.example .env

2. Run with Docker Compose:
   docker compose up -d --build

## Development

- Create virtualenv: python3 -m venv .venv
- Install deps: pip install -r requirements.txt
- Run: python -m src.main
