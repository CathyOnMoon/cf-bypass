import logging
import os
import random
import sys
import cv2
import time
import numpy as np
import pyautogui
import requests
from DrissionPage import ChromiumPage, ChromiumOptions
from image import image_search


class CrossPlatformBypass:
    def _get_chrome_path(self):
        paths = {
            'win32': [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
            ],
            'linux': [
                '/usr/bin/google-chrome',
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser'
            ]
        }
        for path in paths.get(sys.platform, []):
            if os.path.exists(path):
                return path
        return None

    def _setup_browser(self):
        options = ChromiumOptions().auto_port()
        # options.headless()  # 全平台启用无头模式
        options.no_imgs()

        # 设置代理
        proxies = self.fetch_proxies(10, 120)
        if len(proxies) > 0:
            proxy = random.choice(proxies)
            proxy_url = f'http://{proxy}'
            options.set_argument(f'--proxy-server={proxy_url}')
            logging.warning(f'使用代理：{proxy_url}')

        # 平台特定参数
        if sys.platform.startswith('linux'):
            options.set_argument('--no-sandbox')
            options.set_argument('--disable-dev-shm-usage')
        elif sys.platform == 'win32':
            options.set_argument('--disable-gpu-features')

        # 浏览器路径设置
        if chrome_path := self._get_chrome_path():
            options.set_browser_path(chrome_path)

        return ChromiumPage(addr_or_opts=options)

    def solve_challenge(self, target_images: list[str] | str, timeout=60, x_offset=0, y_offset=0):
        start_time = time.time()

        while True:
            try:
                if time.time() - start_time > timeout:
                    logging.error('未找到目标图片：超时')
                    return False
                # 获取并处理截图
                screenshot = pyautogui.screenshot()
                screenshot.save('my_screenshot.png')
                cv2_screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                if cv2_screenshot is None:
                    logging.error('转换屏幕截图失败')
                    return False
                # 图片识别
                images = []
                if isinstance(target_images, str):
                    images.append(target_images)
                else:
                    images.extend(target_images)
                if len(images) == 0:
                    logging.error('未提供目标图片')
                    return False
                for target_img in images:
                    if not os.path.exists(target_img):
                        logging.error(f"目标图片({target_img})不存在")
                        continue
                    target = cv2.imread(target_img)
                    if target is None:
                        logging.error(f"读取目标图片({target_img})失败")
                        continue
                    coords = image_search(cv2_screenshot, target)
                    if len(coords) > 0:
                        logging.warning(f"找到目标图片({target_img})，坐标: {coords}")

                        x = coords[0][0] + x_offset
                        y = coords[0][1] + y_offset
                        # x_center, y_center = pyautogui.locateCenterOnScreen(target_img)
                        # logging.warning(f'x_center：{x_center}, y_center：{y_center}')
                        # logging.warning(f'鼠标当前坐标：{pyautogui.position()}')
                        pyautogui.moveTo(x, y, duration=0.5, tween=pyautogui.easeInElastic)
                        time.sleep(1)
                        pyautogui.click()
                        logging.warning(f'鼠标当前坐标：{pyautogui.position()}')
                        return True
                time.sleep(1)
            except Exception as e:
                logging.error(f"solve challenge error: {str(e)}")
                return False

    def need_verify(self, browser):
        titles = [
            'Just a moment',
            '请稍候'
        ]
        for title in titles:
            if title in browser.title:
                return True
        return False

    def get_cookies(self, url, target_images: list[str] | str, timeout=60, x_offset=0, y_offset=0):
        browser = self._setup_browser()
        try:
            browser.get(url)
            # browser.screencast.set_save_path('video')
            # browser.screencast.set_mode.video_mode()
            # browser.screencast.start()
            if not self.need_verify(browser):
                raise Exception(f"无需验证: {browser.json}")
            if self.solve_challenge(target_images, timeout, x_offset, y_offset):
                start_time = time.time()
                while True:
                    if not self.need_verify(browser):
                        user_agent = browser.user_agent
                        cookies = '; '.join([f"{c['name']}={c['value']}" for c in browser.cookies()])
                        return user_agent, cookies
                    if time.time() - start_time > 10:
                        raise Exception('验证超时')
            raise Exception('未通过验证')
        finally:
            # browser.screencast.stop()
            browser.quit()
            if sys.platform.startswith('linux'):
                self.display.stop()

    def fetch_proxies(self, quantity: int = 10, session_ttl: int = 120):
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


if __name__ == '__main__':
    # 使用示例
    bypass = CrossPlatformBypass()
    start_time = time.time()
    url = 'https://gmgn.ai/api/v1/gas_price/sol'
    target_images = [
        'img/zh-dark.png',
        'img/zh-light.png',
        'img/en-light.png'
    ]
    try:
        user_agent, cookies = bypass.get_cookies(url, target_images, 60, 10, 10)
        logging.warning(f"获取Cookie成功")
        logging.warning(f"User-Agent: {user_agent}, cookies: {cookies}")
    except Exception as e:
        logging.error(f"获取Cookie失败: {str(e)}")
    finally:
        logging.warning(f"耗时: {time.time() - start_time}s")
