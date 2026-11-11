from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Upstream
    SUB_URL: str
    HWID: str

    # Cache & Nodes
    CACHE_TTL_HOURS: int = 24
    CHECK_SCHEDULE_CRON: str = '0 1 * * *'
    TARGET_ALIVE_NODES: int = 5
    REGION_WHITELIST: List[str] = ['Финляндия', 'Нидерланды']
    DIRECT_DOMAINS: List[str] = []

    # Subscription Domain & Endpoint
    SUB_DOMAIN: str = 'sub.example.com'
    PORT: int = 8080
    SUB_SECRET_TOKEN: str

    # Bot platforms
    ENABLE_MATRIX_BOT: bool = True
    ENABLE_TELEGRAM_BOT: bool = False

    # Matrix (configured via .env)
    MATRIX_HOMESERVER: str = ''
    MATRIX_USER_ID: str = ''
    MATRIX_ACCESS_TOKEN: str = ''
    MATRIX_ADMIN_USERS: List[str] = []

    # Telegram (configured via .env)
    TELEGRAM_BOT_TOKEN: str = ''
    TELEGRAM_ADMIN_USERS: List[int] = []
    TELEGRAM_PROXY_URL: str = ''

    # Admin contacts shown once to uninvited users
    ADMIN_CONTACT_TG: str = ''
    ADMIN_CONTACT_MATRIX: str = ''

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
