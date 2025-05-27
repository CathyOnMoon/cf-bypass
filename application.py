import asyncio
import logging
import signal
import sys

from config.config import Config
from core.cookie_pool import CookiePool
from server.server import HttpServer


class Application:
    async def run(self):
        logging.basicConfig(
            format="[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
            level=logging.INFO,
        )

        config = Config()
        config.load_config()

        shutdown_event = asyncio.Event()

        cookie_pool = CookiePool(
            proxy_host=config.proxy_host,
            proxy_username=config.proxy_username,
            proxy_password=config.proxy_password,
            bypass_url=config.bypass_url,
            max_cookie_number=config.max_cookie_number,
            resolve_timeout=config.resolve_timeout,
            click_x_offset=config.click_x_offset,
            click_y_offset=config.click_y_offset,
            user_agent=config.user_agent,
        )

        http_server = HttpServer(shutdown_event, cookie_pool)
        http_server.run(config.port)

        loop = asyncio.get_running_loop()

        def signal_handler():
            logging.warning("接收到退出信号，正在关闭...")
            shutdown_event.set()

        # 跨平台信号处理（关键修改点）
        if sys.platform != 'win32':
            # Unix系统使用原生信号处理
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)
        else:
            # Windows特殊处理方案
            def windows_signal_handler(sig):
                signal_handler()
                loop.call_soon_threadsafe(loop.stop)

            # 使用低层级signal模块注册
            signal.signal(signal.SIGINT, lambda s, f: windows_signal_handler(s))

        # 统一退出逻辑
        try:
            await shutdown_event.wait()
        except KeyboardInterrupt:  # 捕获Windows的Ctrl+C
            shutdown_event.set()

        logging.warning("程序已退出")
