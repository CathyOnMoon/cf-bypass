import asyncio
import logging
import random

import aiohttp
import requests
from DrissionPage._functions.cookies import CookiesList

from core.DrissionPageBypass import DrissionPageBypass


class ProxyCookie:
    def __init__(self, proxy: str, user_agent: str, cookies: CookiesList):
        self.proxy = proxy
        self.user_agent = user_agent
        self.cookies = cookies


class CookiePool:
    def __init__(self):
        self.host = 'https://gmgn.ai/api/v1/gas_price/sol'
        self.cookies: dict[str, ProxyCookie] = {}
        self.bypass = DrissionPageBypass()
        asyncio.create_task(self.task_service())
        logging.info('cookie池已启动')

    def random_cookie(self):
        if not self.cookies:
            return None
        random_key = random.choice(list(self.cookies.keys()))
        random_value = self.cookies[random_key]
        return random_value

    async def task_service(self):
        try:
            while True:
                start_time = asyncio.get_event_loop().time()
                await self.task()
                elapsed = asyncio.get_event_loop().time() - start_time
                await asyncio.sleep(max(60 * 30 - elapsed, 0))  # 确保固定间隔
        except asyncio.CancelledError:
            logging.warning('cookie池已关闭')

    async def task(self):
        proxies = await self.fetch_proxies(quantity=10)
        if not proxies:
            logging.warning('没有可用的代理')
            return
        target_images = [
            'core/img/zh.png',
            'core/img/zh-cn.jpg',
            'core/img/zh-dark.png',
            'core/img/zh-light.png',
            'core/img/en-light.png'
        ]
        for proxy in proxies:
            try:
                loop = asyncio.get_event_loop()
                user_agent, cookies = await loop.run_in_executor(
                    None,  # 使用默认线程池
                    lambda: self.bypass.get_cookies(self.host, proxy, target_images, 60, 10, 10)
                )
                # user_agent, cookies = self.bypass.get_cookies(self.host, proxy, target_images, 60, 10, 10)
                logging.warning(f"获取Cookie成功")
                logging.warning(f"User-Agent: {user_agent}, cookies: {cookies}")
                self.cookies[proxy] = ProxyCookie(proxy, user_agent, cookies)
                logging.warning(f'当前cookie池大小：{len(self.cookies)}')
            except Exception as e:
                logging.error(f"获取Cookie失败: {str(e)}")

    async def fetch_proxies(self, quantity: int = 10, session_ttl: int = 60):
        proxy_api = "https://gw.dataimpulse.com:777/api/list"
        params = {
            'quantity': quantity,
            'type': 'sticky',
            'format': 'hostname:port',
            'session_ttl': session_ttl
        }
        auth = aiohttp.BasicAuth(
            login='9c8787b9721426b1c2f0',
            password='922d1b4d1df80825'
        )
        # resp = requests.get(proxy_api, params=params, auth=auth)
        async with aiohttp.ClientSession() as session:
            async with session.get(proxy_api, params=params, auth=auth) as resp:
                if resp.status != 200:
                    logging.error(f"Failed to get proxy list: {await resp.text()}")
                    return []
                proxy_list = (await resp.text()).strip().split('\n')
                proxies = []
                for proxy in proxy_list:
                    if not proxy.strip():
                        continue
                    parts = proxy.strip().split(':')
                    if len(parts) != 2:
                        logging.error(f'代理格式错误: {proxy}')
                        continue
                    ip, port = parts
                    if not port.isdigit():
                        logging.error(f'代理端口错误: {proxy}')
                        continue
                    proxies.append(proxy)
                return proxies
