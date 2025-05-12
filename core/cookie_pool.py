import json
import os
from datetime import datetime

from core.proxy_ip import ProxyIP
from core.proxy_manager import ProxyManager


class CookiePool:
  def __init__(self, pool_file='cookie_pool.json', min_pool_size=3):
    self.pool_file = pool_file
    self.cookies = []
    self.min_pool_size = min_pool_size
    self.current_index = 0
    self.proxy_manager = ProxyManager()
    self.load_cookies()

  def load_cookies(self):
    if os.path.exists(self.pool_file):
      try:
        with open(self.pool_file, 'r') as f:
          data = json.load(f)
          self.cookies = data.get('cookies', [])
          # 加载代理
          for proxy_data in data.get('proxies', []):
            proxy = ProxyIP.from_dict(proxy_data)
            self.proxy_manager.proxies.append(proxy)
      except Exception as e:
        print(f"加载cookie时出错: {e}")
        self.cookies = []

  def save_cookies(self):
    data = {
      'cookies': self.cookies,
      'proxies': [p.to_dict() for p in self.proxy_manager.proxies]
    }
    with open(self.pool_file, 'w') as f:
      json.dump(data, f)

  def add_cookie(self, user_agent, cookie, proxy):
    # 检查cookie是否已存在
    for existing in self.cookies:
      if existing['cookie'] == cookie:
        return False

    cookie_data = {
      'user_agent': user_agent,
      'cookie': cookie,
      'created_at': datetime.now().isoformat(),
      'proxy_ip': proxy.ip,
      'proxy_port': proxy.port
    }
    self.cookies.append(cookie_data)
    proxy.add_cookie(cookie)
    self.save_cookies()
    print(f"添加新cookie。当前池大小: {len(self.cookies)}")
    return True

  def get_next_cookie(self):
    if not self.cookies:
      return None, None, None

    # 获取当前cookie
    current_cookie = self.cookies[self.current_index]

    # 更新索引实现轮询
    self.current_index = (self.current_index + 1) % len(self.cookies)

    # 获取关联的代理
    proxy = self.proxy_manager.get_proxy_for_cookie(current_cookie['cookie'])

    return current_cookie['user_agent'], current_cookie['cookie'], proxy

  def remove_cookie(self, cookie):
    for i, cookie_data in enumerate(self.cookies):
      if cookie_data['cookie'] == cookie:
        # 从代理中移除
        proxy = self.proxy_manager.get_proxy_for_cookie(cookie)
        if proxy:
          proxy.remove_cookie(cookie)

        # 从cookie列表中移除
        self.cookies.pop(i)

        # 如果需要，调整current_index
        if i <= self.current_index:
          self.current_index = max(0, self.current_index - 1)
        if self.current_index >= len(self.cookies):
          self.current_index = 0

        self.save_cookies()
        print(f"移除过期cookie。当前池大小: {len(self.cookies)}")
        break

  def get_pool_size(self):
    return len(self.cookies)

  def needs_replenishment(self):
    current_size = self.get_pool_size()
    needs = current_size < self.min_pool_size
    if needs:
      print(
        f"池需要补充。当前大小: {current_size}, 目标大小: {self.min_pool_size}")
    return needs