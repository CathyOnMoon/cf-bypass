import asyncio
import logging
import signal
from server.server import HttpServer


class Application:
    async def run(self):
        logging.basicConfig(
            format="[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
            level=logging.INFO,
        )

        shutdown_event = asyncio.Event()

        http_server = HttpServer(shutdown_event)
        http_server.run()

        loop = asyncio.get_running_loop()

        def signal_handler():
            logging.warning("接收到退出信号，正在关闭...")
            shutdown_event.set()

        # 使用异步信号处理
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        await shutdown_event.wait()
        logging.warning("程序已退出")
