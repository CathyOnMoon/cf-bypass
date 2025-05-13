import asyncio
import logging
import signal
from server.server import HttpServer


class Application:
    async def run(self):
        shutdown_event = asyncio.Event()

        http_server = HttpServer(shutdown_event)
        http_server.run()

        def signal_handler(sig, frame):
            logging.warning(f"接收到信号 {sig}, 正在退出...")
            shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 等待关闭事件
        await shutdown_event.wait()
        logging.warning("程序已退出")