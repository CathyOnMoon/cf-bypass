import time

from playwright.sync_api import sync_playwright, ProxySettings

if __name__ == '__main__':
    with sync_playwright() as p:
        # 启动浏览器，设置代理
        proxy_settings = ProxySettings({
            "server": "http://superproxy.zenrows.com:1337",  # 代理地址和端口
            "username": "7Mh7Hyrdx3Hb",
            "password": "D6D7EKLnhe6gC6T_region-ap"
        })
        browser = p.chromium.launch(
            proxy=proxy_settings,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",  # 隐藏自动化标识
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
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        )
        # 创建新页面并跳转
        page = context.new_page()
        page.goto("https://gmgn.ai/api/v1/gas_price/sol", timeout=60000)
        page.wait_for_timeout(5000)
        time.sleep(30)

        # 关闭浏览器
        browser.close()

