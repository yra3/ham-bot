import asyncio
import logging
import uvicorn
from src.config import settings
from src.core import db
from src.core.checker import NodeHealthChecker
from src.core.fetcher import SubscriptionFetcher
from src.generators.xray import sync_sidecar_xray_config
from src.web.app import app
from src.bot.matrix import MatrixBotService
from src.bot.telegram import TelegramBotService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('ham-bot')


async def run_web():
    config = uvicorn.Config(app=app, host='0.0.0.0', port=settings.PORT, log_level='info')
    server = uvicorn.Server(config)
    await server.serve()


async def run_matrix():
    if not settings.ENABLE_MATRIX_BOT:
        logger.info('Matrix bot is disabled by configuration.')
        return
    logger.info('Starting Matrix bot service...')
    bot = MatrixBotService()
    await bot.start()


async def run_telegram():
    if not settings.ENABLE_TELEGRAM_BOT:
        logger.info('Telegram bot is disabled by configuration.')
        return
    logger.info('Starting Telegram bot service...')
    bot = TelegramBotService()
    await bot.start()


async def run_scheduler(fetcher: SubscriptionFetcher, checker: NodeHealthChecker):
    while True:
        await asyncio.sleep(3600)
        try:
            if not fetcher.is_cache_valid():
                logger.info('Subscription cache expired; refreshing from upstream...')
                await fetcher.fetch(force=False)
                await sync_sidecar_xray_config(fetcher, checker, settings.REGION_WHITELIST)
        except Exception as e:
            logger.error(f'Background subscription refresh failed: {e}')


async def main():
    logger.info('Initializing SQLite storage...')
    db.init_db()

    fetcher = SubscriptionFetcher(
        sub_url=settings.SUB_URL,
        hwid=settings.HWID,
        cache_ttl_hours=settings.CACHE_TTL_HOURS,
    )
    checker = NodeHealthChecker(target_alive=settings.TARGET_ALIVE_NODES)
    try:
        await sync_sidecar_xray_config(fetcher, checker, settings.REGION_WHITELIST)
    except Exception as e:
        logger.warning(f'Initial sidecar xray sync warning: {e}')

    logger.info('Starting ham-bot application...')
    tasks = [
        asyncio.create_task(run_web()),
        asyncio.create_task(run_matrix()),
        asyncio.create_task(run_telegram()),
        asyncio.create_task(run_scheduler(fetcher, checker)),
    ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
