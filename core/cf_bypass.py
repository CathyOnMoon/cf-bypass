import logging
import time

import numpy as np
import pyautogui
from DrissionPage._configs.chromium_options import ChromiumOptions
from DrissionPage._pages.chromium_page import ChromiumPage
import cv2

from core.image import image_search


class CloudflareBypass:
    language_dict = {
        'en-us': {'title': 'Just a moment'},
        'zh-cn': {'title': '请稍候'},
    }

    image_path_dict = {
        'zh-cn': 'img/zh-cn.jpg'
    }

    def __init__(self, browser_path):
        self.browser_path = browser_path
        self.image_dict = {}
        for key, value in self.image_path_dict.items():
            self.image_dict[key] = cv2.imread(value)

    def _setup_browser(self, proxy=None):
        options = ChromiumOptions().auto_port()
        options.set_paths(self.browser_path)
        # 无头模式
        # options.headless()
        # options.no_imgs()
        # options.set_argument('--disable-gpu')
        # Linux必需参数
        # options.set_argument('--no-sandbox')
        # options.set_argument('--disable-dev-shm-usage')

        args = [
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

        for arg in args:
            options.set_argument(arg)

        return ChromiumPage(addr_or_opts=options)

    def check_cookie_valid(self, response):
        for lang_dict in self.language_dict.values():
            if lang_dict['title'] in response.text:
                return False
        return True

    def _is_bypassed(self, driver):
        for dict in self.language_dict.values():
            if dict['title'] in driver.title:
                return False
        return True

    def _click_button(self, driver, x, y):
        print('点击绕过cloudflare按钮')

        click_x = x + driver.rect.page_location[0] + 10
        click_y = y + driver.rect.page_location[1] + 10
        print(f'点击坐标: x={click_x}, y={click_y}')

        pyautogui.moveTo(click_x, click_y, duration=0.5, tween=pyautogui.easeInElastic)
        pyautogui.click()

    def _cookie_format_convert(self, driver_cookie):
        requests_cookie = ''
        for dict in driver_cookie:
            requests_cookie += f'{dict["name"]}={dict["value"]}; '
        return requests_cookie

    def generate_cookie(self, url):
        driver = self._setup_browser()
        try:
            driver.get(url)
            # is_clicked = False

            # while not self._is_bypassed(driver):
            #     image = driver.get_screenshot(as_bytes='jpg')
            #     image = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
            #     # 保存图片到相对目录
            #     cv2.imwrite('img/screenshot.jpg', image)
            #
            #     for target in self.image_dict.values():
            #         coords = image_search(image, target)
            #         print('finding', coords)
            #         if not is_clicked and len(coords) == 1:
            #             self._click_button(driver, coords[0][0], coords[0][1])
            #             is_clicked = True

            if not self._handle_cloudflare_challenge(driver):
                raise Exception("Cloudflare challenge failed")

            user_agent = driver.user_agent
            cookies = self._cookie_format_convert(driver.cookies())
            return user_agent, cookies
        except Exception as e:
            logging.error(f"生成cookie失败: {str(e)}")
            return None, None
        finally:
            driver.quit()

    def _handle_cloudflare_challenge(self, page):
        """处理Cloudflare验证挑战"""
        max_retries = 3
        for _ in range(max_retries):
            if self._is_bypassed(page):
                return True

            # 使用更可靠的选择器定位验证按钮
            verify_btn = page.ele('xpath://*[@id="challenge-stage"]//*[contains(text(), "Verify")]', timeout=5)
            if verify_btn:
                verify_btn.click()
                page.wait.load_start()
                time.sleep(3)
            else:
                # 尝试通过执行JavaScript触发验证
                page.run_js('''
                    const cf = document.querySelector("#challenge-form");
                    if (cf) cf.submit();
                ''')
                time.sleep(5)

        return self._is_bypassed(page)
