import asyncio
import logging

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
        proxies = {
            "http": f"http://{cookie.proxy}",  # HTTP 代理
            "https": f"http://{cookie.proxy}",  # HTTPS 代理
        }
        resp = requests.get(url, proxies=proxies, headers={
            'User-Agent': cookie.user_agent,
            'cookie': cookie.cookies.as_str(),
        })
        try:
            json_resp = resp.json()
            return web.json_response(json_resp)
        except Exception as e:
            return web.json_response({
                'code': 500,
                'message': 'failed',
                'proxy': cookie.proxy,
                'cookie': cookie.cookies.as_str(),
                '_cookie': cookie.cookies.as_str(),
                'User-Agent': cookie.user_agent,
                'resp': resp.text
            }, status=500)

    def format_cookie(self, driver_cookie):
        requests_cookie = ''
        for dict in driver_cookie:
            requests_cookie += f'{dict["name"]}={dict["value"]}; '
        return requests_cookie
