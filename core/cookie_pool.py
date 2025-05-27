import asyncio
import json
import logging
import os
import random
import string
from typing import List
from core.PlaywrightBypass import PlaywrightBypass


class ProxyCookie:
    def __init__(self, proxy: str, user_agent: str, cookies: str):
        self.proxy = proxy
        self.user_agent = user_agent
        self.cookies = cookies


class CookiePool:
    def __init__(
        self,
        proxy_host: str,
        proxy_username: str,
        proxy_password: str,
        bypass_url: str,
        max_cookie_number=10,
        resolve_timeout=60,
        click_x_offset=10,
        click_y_offset=10,
        user_agent: str | None = None,
        cache_file: str = "cookies.json"
    ):

        self.proxy_host = proxy_host
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.bypass_url = bypass_url
        self.max_cookie_number = max_cookie_number
        self.resolve_timeout = resolve_timeout
        self.click_x_offset = click_x_offset
        self.click_y_offset = click_y_offset
        self.user_agent = user_agent
        self.cookie_list: List[ProxyCookie] = []
        self.cache_file = cache_file
        self.target_images = [
            'core/img/zh.png',
            'core/img/zh-cn.jpg',
            'core/img/zh-dark.png',
            'core/img/zh-light.png',
            'core/img/en-light.png'
        ]
        self.bypass = PlaywrightBypass()
        self.running = False
        self.load_from_cache()
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
        if len(self.cookie_list) >= self.max_cookie_number:
            return
        self.running = True
        quantity = self.max_cookie_number - len(self.cookie_list)
        proxies = self.generate_proxies(quantity=quantity)

        for proxy in proxies:
            try:
                loop = asyncio.get_event_loop()
                user_agent, cookies = await loop.run_in_executor(
                    None,  # 使用默认线程池
                    lambda: self.bypass.resolve(
                        self.bypass_url,
                        proxy,
                        self.target_images,
                        self.user_agent,
                        self.resolve_timeout,
                        self.click_x_offset,
                        self.click_y_offset
                    )
                )
                cookie = '; '.join([f'{c["name"]}={c["value"]}' for c in cookies])
                self.cookie_list.append(ProxyCookie(proxy, user_agent, cookie))
                # logging.info(f"获取Cookie成功")
                # logging.info(f"User-Agent: {user_agent}, cookies: {cookies}")
                # logging.info(f'当前cookie池大小：{len(self.cookie_list)}')
            except Exception as e:
                logging.error(f"获取Cookie失败: {str(e)}")
        self.running = False

    def generate_proxies(self, quantity: int = 10):
        proxies = []
        for i in range(quantity):
            random_session = self.generate_random_string(length=8)
            proxy_username = self.proxy_username.format(session_id=random_session)
            proxy_password = self.proxy_password.format(session_id=random_session)
            proxy = f"https://{proxy_username}:{proxy_password}@{self.proxy_host}"
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

    def load_from_cache(self):
        """从JSON文件加载缓存的Cookies"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cookie_list = [
                        ProxyCookie(
                            proxy=item['proxy'],
                            user_agent=item['user_agent'],
                            cookies=item['cookies']
                        ) for item in data if all(key in item for key in ('proxy', 'user_agent', 'cookies'))
                    ]
                logging.info(f"从缓存加载了{len(self.cookie_list)}个Cookies")
        except Exception as e:
            logging.error(f"加载缓存失败: {str(e)}")

    def save_to_cache(self):
        """保存当前Cookies到JSON文件"""
        try:
            data = [
                {
                    "proxy": pc.proxy,
                    "user_agent": pc.user_agent,
                    "cookies": pc.cookies
                } for pc in self.cookie_list
            ]
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # logging.info(f"成功保存{len(data)}个Cookies到缓存")
        except Exception as e:
            logging.error(f"保存缓存失败: {str(e)}")
