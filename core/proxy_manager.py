import random
from datetime import timedelta, datetime

from core.proxy_ip import ProxyIP


class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.last_fetch_time = None
        self.fetch_interval = timedelta(minutes=25)  # 在当前代理过期前获取新代理

    def fetch_proxies(self):
        if (self.last_fetch_time is None or
                datetime.now() - self.last_fetch_time > self.fetch_interval):
            try:
                # 生成100个代理
                self.proxies = []
                for _ in range(100):
                    # 生成随机的session ID (16位数字和字母组合)
                    session_id = ''.join(random.choices('0123456789abcdef', k=16))

                    # 构建代理字符串
                    proxy_str = f"customer-4c3229ea54d-session-{session_id}-time-30:5af3929c@proxy.shenlongproxy.com:31212"

                    try:
                        # 解析代理字符串
                        auth_part, host_part = proxy_str.strip().split('@')
                        username, password = auth_part.split(':')
                        hostname, port = host_part.split(':')

                        # 验证端口号
                        if not port.isdigit():
                            print(f"Skipping invalid port number: {port}")
                            continue

                        # 创建代理对象并添加到列表
                        self.proxies.append(ProxyIP(hostname, port, username, password))
                    except Exception as e:
                        print(f"Error processing proxy {proxy_str}: {e}")
                        continue

                self.last_fetch_time = datetime.now()
                print(f"Successfully generated {len(self.proxies)} proxies")
                return True
            except Exception as e:
                print(f"生成代理时出错: {e}")
        return False

    def get_available_proxy(self):
        # 移除过期的代理
        self.proxies = [p for p in self.proxies if not p.is_expired()]

        # 如果没有可用代理，获取新的
        if not self.proxies:
            self.fetch_proxies()

        # 返回一个可以接受更多cookie的随机代理
        available_proxies = [p for p in self.proxies if p.can_add_cookie()]
        return random.choice(available_proxies) if available_proxies else None

    def get_proxy_for_cookie(self, cookie):
        for proxy in self.proxies:
            if cookie in proxy.cookies:
                return proxy
        return None

    def remove_expired_proxies(self):
        expired_proxies = [p for p in self.proxies if p.is_expired()]
        for proxy in expired_proxies:
            self.proxies.remove(proxy)
        return len(expired_proxies)