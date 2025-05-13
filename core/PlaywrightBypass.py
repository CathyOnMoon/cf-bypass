import logging
import os
import cv2
import time
import numpy as np
import pyautogui
import requests
from playwright.sync_api import sync_playwright, ProxySettings

from image import image_search


class PlaywrightBypass:
    def solve_challenge(self, target_images: list[str] | str, timeout=60, x_offset=0, y_offset=0):
        start_time = time.time()

        while True:
            try:
                if time.time() - start_time > timeout:
                    logging.error('未找到目标图片：超时')
                    return False
                # 获取并处理截图
                screenshot = pyautogui.screenshot()
                # screenshot.save('screenshot.png')
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
                        # logging.warning(f'鼠标当前坐标：{pyautogui.position()}')
                        return True
                time.sleep(1)
            except Exception as e:
                logging.error(f"solve challenge error: {str(e)}")
                return False

    def need_verify(self, page_title):
        titles = [
            'Just a moment',
            '请稍候'
        ]
        for title in titles:
            if title in page_title:
                return True
        return False

    def get_cookies(self, target_url, proxy: ProxySettings | None, target_images: list[str] | str, timeout=60, x_offset=0,
                    y_offset=0):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                proxy=proxy,
                headless=False,
                args=[
                    # "--disable-blink-features=AutomationControlled",  # 隐藏自动化标识
                    "-no-first-run",
                    "-force-color-profile=srgb",
                    "-metrics-recording-only",
                    "-password-store=basic",
                    "-use-mock-keychain",
                    "-export-tagged-pdf",
                    "-no-default-browser-check",
                    "-disable-background-mode",
                    "-enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions",
                    "-disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage",
                    "-deny-permission-prompts",
                    "-disable-gpu",
                ]
            )
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
            context = browser.new_context(
                user_agent=user_agent,
            )
            # 创建新页面并跳转
            page = context.new_page()
            page.context.clear_cookies()
            page.goto(target_url, timeout=60000)
            page.wait_for_load_state("load")
            try:
                if not self.need_verify(page.title()):
                    raise Exception(f"无需验证: {page.content()}")
                if self.solve_challenge(target_images, timeout, x_offset, y_offset):
                    start_time = time.time()
                    while True:
                        if page.is_closed():
                            raise Exception('页面已关闭')

                        try:
                            current_title = page.title()
                        except Exception as e:
                            # 处理执行上下文错误，等待新页面加载
                            page.wait_for_load_state("load")
                            current_title = page.title()

                        if not self.need_verify(current_title):
                            return user_agent, page.context.cookies()

                        if time.time() - start_time > 10:
                            raise Exception('验证超时')

                        # 避免过快轮询
                        page.wait_for_timeout(500)
                raise Exception('未找到点击坐标')
            finally:
                page.close()


if __name__ == '__main__':
    # 使用示例
    bypass = PlaywrightBypass()
    start_time = time.time()
    url = 'https://gmgn.ai/api/v1/gas_price/sol'
    target_images = [
        'img/zh.png',
        'img/zh-cn.jpg',
        'img/zh-dark.png',
        'img/zh-light.png',
        'img/en-light.png'
    ]
    try:
        proxy_host = 'superproxy.zenrows.com:1337'
        proxy_username = '7Mh7Hyrdx3Hb'
        proxy_password = 'D6D7EKLnhe6gC6T_ttl-1m_session-gtgegwhr5u46'
        proxy = ProxySettings({
            "server": f"http://{proxy_host}",  # 代理地址和端口
            "username": proxy_username,
            "password": proxy_password
        })
        user_agent, cookies = bypass.get_cookies(url, proxy, target_images, 60, 12, 15)
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        logging.warning(f"获取Cookie成功: {cookie_str}")
        proxies = {
            "http": f"http://{proxy_username}:{proxy_password}@{proxy_host}",
            "https": f"http://{proxy_username}:{proxy_password}@{proxy_host}",
        }
        resp = requests.get(url, proxies=proxies, headers={
            'user-agent': user_agent,
            'cookie': cookie_str,
        })
        logging.warning(f"响应: {resp.text}")
    except Exception as e:
        logging.error(f"获取Cookie失败: {str(e)}")
    finally:
        logging.warning(f"耗时: {time.time() - start_time}s")
