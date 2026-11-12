from pydantic_settings import BaseSettings, SettingsConfigDict
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
    SUB_BASE_URL: str = ''
    SUB_SCHEME: str = 'https'
    SUB_DOMAIN: str = 'sub.example.com'
    HOST_PORT: int = 8088
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
    PROXY_BIND_HOST: str = '127.0.0.1'

    # Admin contacts shown once to uninvited users
    ADMIN_CONTACT_TG: str = ''
    ADMIN_CONTACT_MATRIX: str = ''

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    def get_sub_base_url(self) -> str:
        raw = (self.SUB_BASE_URL or '').strip().rstrip('/')
        if raw:
            if '://' in raw:
                return raw
            return f'{self.SUB_SCHEME}://{raw}'
        dom = (self.SUB_DOMAIN or '').strip().rstrip('/')
        if '://' in dom:
            return dom
        return f'{self.SUB_SCHEME}://{dom}'

    def build_sub_url(self, token: str, endpoint: str = 'verified-smart') -> str:
        return f'{self.get_sub_base_url()}/s/{token}/{endpoint}'


settings = Settings()
