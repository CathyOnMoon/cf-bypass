import asyncio
import logging
import random
import string
from typing import List

from patchright.sync_api import Cookie

from core.PlaywrightBypass import PlaywrightBypass


class ProxyCookie:
    def __init__(self, proxy: str, user_agent: str, cookies: List[Cookie]):
        self.proxy = proxy
        self.user_agent = user_agent
        self.cookies = cookies


class CookiePool:
    def __init__(self):
        self.host = 'https://gmgn.ai/api/v1/gas_price/sol'
        self.cookie_list: List[ProxyCookie] = []
        self.bypass = PlaywrightBypass()
        self.running = False
        asyncio.create_task(self.task())
        logging.info('cookie池已启动')

    async def task(self):
        try:
            while True:
                if not self.running:
                    await self.generate_cookies()
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            logging.warning('cookie池已关闭')

    async def generate_cookies(self):
        max_cookie_number = 10
        if len(self.cookie_list) >= max_cookie_number:
            return
        self.running = True
        quantity = max_cookie_number - len(self.cookie_list)
        proxies = self.generate_proxies(quantity=quantity)
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
                    lambda: self.bypass.resolve(self.host, proxy, target_images, 60, 10, 10)
                )
                self.cookie_list.append(ProxyCookie(proxy, user_agent, cookies))
                logging.info(f"获取Cookie成功")
                # logging.info(f"User-Agent: {user_agent}, cookies: {cookies}")
                logging.info(f'当前cookie池大小：{len(self.cookie_list)}')
            except Exception as e:
                logging.error(f"获取Cookie失败: {str(e)}")
        self.running = False

    def generate_proxies(self, quantity: int = 10, session_ttl: str = '30m'):
        proxies = []
        proxy_host = 'superproxy.zenrows.com:1337'
        proxy_username = '7Mh7Hyrdx3Hb'
        for i in range(quantity):
            random_session = self.generate_random_string()
            proxy_password = f'D6D7EKLnhe6gC6T_ttl-{session_ttl}_session-{random_session}'
            proxy = f"http://{proxy_username}:{proxy_password}@{proxy_host}"
            if proxy not in proxies:
                proxies.append(proxy)
        return proxies

    def generate_random_string(self, length=12):
        characters = string.ascii_letters
        return ''.join(random.choice(characters) for _ in range(length))

    def random_cookie(self) -> ProxyCookie | None:
        if len(self.cookie_list) == 0:
            return None
        proxy_cookie: ProxyCookie = random.choice(self.cookie_list)
        return proxy_cookie

    def remove_cookie(self, cookie: ProxyCookie):
        if cookie in self.cookie_list:
            self.cookie_list.remove(cookie)