import time

from playwright.sync_api import sync_playwright, ProxySettings

if __name__ == '__main__':
    with sync_playwright() as p:
        # 启动浏览器，设置代理
        proxy_settings = ProxySettings({
            "server": "http://superproxy.zenrows.com:1337",  # 代理地址和端口
            "username": "7Mh7Hyrdx3Hb",  # 若需要认证
            "password": "KTwhyriwVqLm9kd_region-ap"  # 若需要认证
        })
        browser = p.chromium.launch(
            # proxy=proxy_settings,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",  # 隐藏自动化标识
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        )
        # 创建新页面并跳转
        page = browser.new_page()
        page.goto("https://gmgn.ai/api/v1/gas_price/sol", timeout=60000)

        time.sleep(60)

        # 关闭浏览器
        browser.close()

