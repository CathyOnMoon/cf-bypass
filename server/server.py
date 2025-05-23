import asyncio
import logging
from urllib.parse import unquote

import aiohttp
from aiohttp import web

from core.cookie_pool import CookiePool


class HttpServer:
    def __init__(self, shutdown_event: asyncio.Event, cookie_pool: CookiePool):
        self.shutdown_event = shutdown_event
        self.cookie_pool = cookie_pool

    def run(self, port: int):
        host = '0.0.0.0'
        asyncio.create_task(self.start_server(port, host))

    async def start_server(self, port: int, host='0.0.0.0'):
        app = web.Application()
        app.router.add_get('/fetch', self.fetch)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
        logging.warning(f"http服务已启动：{host}:{port}")
        try:
            await self.shutdown_event.wait()
        finally:
            # 正确关闭服务器和清理资源
            await site.stop()
            await runner.cleanup()
            await app.cleanup()
            logging.warning("HTTP服务已关闭")

    async def fetch(self, request: web.Request):
        url = request.query.get('url')
        if not url or not url.startswith('http'):
            return web.json_response({
                'code': 400,
                'message': 'url参数错误'
            })
        url = unquote(url)
        try:
            max_retries = 3
            for retry in range(max_retries):
                proxy_cookie = self.cookie_pool.random_cookie()
                if not proxy_cookie:
                    return web.json_response({
                        'code': 500,
                        'message': 'no cookies'
                    })
                headers = {
                    'User-Agent': proxy_cookie.user_agent,
                    'cookie': proxy_cookie.cookies,
                }
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, proxy=proxy_cookie.proxy, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        resp_content = await resp.text()
                        if 'Just a moment' in resp_content:
                            self.cookie_pool.remove_cookie(proxy_cookie)
                            continue
                        return web.Response(text=resp_content)
            raise Exception("Failed to bypass Cloudflare protection after maximum retries")
        except Exception as e:
            return web.json_response({
                'code': 500,
                'message': str(e)
            }, status=500)


