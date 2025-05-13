import asyncio
import logging
import random

import requests
from DrissionPage._functions.cookies import CookiesList

from core.bypass import CrossPlatformBypass


class ProxyCookie:
    def __init__(self, proxy: str, user_agent: str, cookies: CookiesList):
        self.proxy = proxy
        self.user_agent = user_agent
        self.cookies = cookies


class CookiePool:
    def __init__(self):
        self.host = 'https://gmgn.ai/api/v1/gas_price/sol'
        self.cookies: dict[str, ProxyCookie] = {}
        self.bypass = CrossPlatformBypass()
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
                await self.task()
                await asyncio.sleep(60 * 10)
        except asyncio.CancelledError:
            logging.warning('cookie池已关闭')

    async def task(self):
        proxies = await self.fetch_proxies()
        if not proxies:
            logging.warning('没有可用的代理')
            return
        target_images = [
            'img/zh.png',
            'img/zh-cn.jpg',
            'img/zh-dark.png',
            'img/zh-light.png',
            'img/en-light.png'
        ]
        for proxy in proxies:
            try:
                user_agent, cookies = self.bypass.get_cookies(self.host, proxy, target_images, 60, 10, 10)
                logging.warning(f"获取Cookie成功")
                logging.warning(f"User-Agent: {user_agent}, cookies: {cookies}")
                self.cookies[proxy] = ProxyCookie(proxy, user_agent, cookies)
                logging.warning(f'当前cookie池大小：{len(self.cookies)}')
            except Exception as e:
                logging.error(f"获取Cookie失败: {str(e)}")

    async def fetch_proxies(self, quantity: int = 10, session_ttl: int = 120):
        proxy_api = "https://gw.dataimpulse.com:777/api/list"
        params = {
            'quantity': quantity,
            'type': 'sticky',
            'format': 'hostname:port',
            'session_ttl': session_ttl
        }
        auth = ('9c8787b9721426b1c2f0', '922d1b4d1df80825')
        resp = requests.get(proxy_api, params=params, auth=auth)
        if resp.status_code != 200:
            logging.error(f"Failed to get proxy list: {resp.text}")
            return []
        proxies = []
        proxy_list = resp.text.strip().split('\n')
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
