import asyncio
import logging

import aiohttp
import requests
from aiohttp import web

from core.cookie_pool import CookiePool


class HttpServer:
    def __init__(self, shutdown_event: asyncio.Event):
        self.shutdown_event = shutdown_event
        self.cookie_pool = CookiePool()

    def run(self):
        host = '0.0.0.0'
        port = 7963
        asyncio.create_task(self.start_server(host, port))
        logging.warning(f"http服务已启动：{host}:{port}")

    async def start_server(self, host='0.0.0.0', port=7963):
        app = web.Application()
        app.router.add_get('/fetch', self.fetch)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        await self.shutdown_event.wait()
        logging.warning("http服务已关闭")

    async def fetch(self, request: web.Request):
        url = request.query.get('url')
        if not url or not url.startswith('http'):
            return web.json_response({
                'code': 400,
                'message': 'url参数错误'
            })
        cookie = self.cookie_pool.random_cookie()
        if not cookie:
            return web.json_response({
                'code': 500,
                'message': '获取cookie失败'
            })
        headers = {
            'User-Agent': cookie.user_agent,
            'cookie': self.format_cookie(cookie.cookies),
        }
        async with aiohttp.ClientSession() as session:
          async with session.get(url,headers=headers,
              proxy=f"http://{cookie.proxy}",
              timeout=aiohttp.ClientTimeout(total=30)
          ) as resp:
            try:
                json_resp = await resp.json()
                return web.json_response(json_resp)
            except Exception as e:
                return web.json_response({
                    'code': 500,
                    'message': 'failed',
                    'proxy': cookie.proxy,
                    'cookie': cookie.cookies.as_str(),
                    '_cookie': self.format_cookie(cookie.cookies),
                    'User-Agent': cookie.user_agent,
                    'resp': resp.text
                }, status=500)

    def format_cookie(self, driver_cookie):
        requests_cookie = ''
        for dict in driver_cookie:
            requests_cookie += f'{dict["name"]}={dict["value"]}; '
        return requests_cookie
