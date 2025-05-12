import asyncio
import logging
from aiohttp import web

from core.cf_bypass import CloudflareBypass


class HttpServer:
    def __init__(self, shutdown_event: asyncio.Event, cf_bypass: CloudflareBypass):
        self.shutdown_event = shutdown_event
        self.cf_bypass = cf_bypass

    def run(self):
        host = '0.0.0.0'
        port = 7963
        asyncio.create_task(self.start_server(host, port))
        logging.warning(f"http服务已启动：{host}:{port}")

    async def start_server(self, host='0.0.0.0', port=7963):
        app = web.Application()
        app.router.add_get('/proxy', self.proxy)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        await self.shutdown_event.wait()
        logging.warning("http服务已关闭")

    async def proxy(self, request: web.Request):
        url = request.query.get('url')
        logging.warning(f"收到代理请求：{url}")
        if not url or not url.startswith('http'):
            return web.json_response({
                'code': 400,
                'message': 'url参数错误'
            })
        user_agent, cookie = self.cf_bypass.generate_cookie(url)
        return web.json_response({
            'code': 200,
            'message': 'success',
            'data': {
                'user_agent': user_agent,
                'cookie': cookie
            }
        })
