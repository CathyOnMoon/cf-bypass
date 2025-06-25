import asyncio
import logging
import ssl
from urllib.parse import unquote

import aiohttp
from aiohttp import web

from core.cookie_pool import CookiePool


class HttpServer:
    def __init__(self, shutdown_event: asyncio.Event, cookie_pool: CookiePool):
        self.shutdown_event = shutdown_event
        self.cookie_pool = cookie_pool
        # 创建自定义 SSL 上下文（允许 TLS 1.0+）
        self.ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1  # 允许 TLS 1.0
        self.ssl_ctx.set_ciphers("DEFAULT@SECLEVEL=1")  # 降低加密强度

    def run(self, port: int):
        host = '0.0.0.0'
        asyncio.create_task(self.start_server(port, host))

    async def start_server(self, port: int, host='0.0.0.0'):
        app = web.Application()
        app.router.add_get('/fetch', self.fetch)
        app.router.add_get('/cookies', self.cookies)
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
        max_retries = 3
        for retry in range(max_retries):
            proxy_cookie = self.cookie_pool.random_cookie()
            if not proxy_cookie:
                return web.json_response({
                    'code': 500,
                    'message': 'no cookies'
                })
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'max-age=0',
                'Cookie': proxy_cookie.cookies,
                'Sec-Ch-Ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                'Sec-Ch-Ua-Arch': '"x86"',
                'Sec-Ch-Ua-Bitness': '"64"',
                'Sec-Ch-Ua-Full-Version': '"119.0.6045.159"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Linux"',
                'Sec-Ch-Ua-Platform-Version': '"6.8.0"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': proxy_cookie.user_agent,
            }
            try:
                async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(ssl=False),
                    trust_env=False
                ) as session:
                    async with session.get(
                        url,
                        headers=headers,
                        proxy=proxy_cookie.proxy,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        resp_content = await resp.text()
                        if 'Just a moment' in resp_content:
                            logging.error(f"cookie已失效，移除代理cookie: {proxy_cookie.proxy}")
                            self.cookie_pool.remove_cookie(proxy_cookie)
                            continue
                        return web.Response(text=resp_content)
            except aiohttp.ClientSSLError as e:
                logging.error(f"SSL错误：{str(e)}，移除代理cookie: {proxy_cookie.proxy}")
                self.cookie_pool.remove_cookie(proxy_cookie)
                continue
            except aiohttp.ClientProxyConnectionError as e:
                logging.error(f"代理连接失败：{str(e)}，移除代理cookie: {proxy_cookie.proxy}")
                self.cookie_pool.remove_cookie(proxy_cookie)
                continue
            except Exception as e:
                logging.error(f"请求失败：{str(e)}")
                # self.cookie_pool.remove_cookie(proxy_cookie)
                continue
        return web.json_response({
            'code': 500,
            'message': '超出最大请求次数'
        }, status=500)

    async def cookies(self, request: web.Request):
        try:
            return web.json_response({
                'code': 200,
                'message': 'success',
                'data': {
                    'cookies': len(self.cookie_pool.cookie_list)
                }
            })
        except Exception as e:
            return web.json_response({
                'code': 500,
                'message': str(e)
            }, status=500)

