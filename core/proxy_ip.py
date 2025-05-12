from datetime import datetime, timedelta


class ProxyIP:
  def __init__(self, ip, port, username=None, password=None, created_at=None):
    self.ip = ip
    self.port = port
    self.username = username
    self.password = password
    self.created_at = created_at or datetime.now()
    self.cookies = []  # 与该IP关联的cookie列表
    self.max_cookies = 10  # 每个IP最多可关联的cookie数量

  def is_expired(self):
    return datetime.now() - self.created_at > timedelta(minutes=30)

  def can_add_cookie(self):
    return len(self.cookies) < self.max_cookies

  def add_cookie(self, cookie):
    if self.can_add_cookie():
      self.cookies.append(cookie)
      return True
    return False

  def remove_cookie(self, cookie):
    if cookie in self.cookies:
      self.cookies.remove(cookie)

  def to_dict(self):
    return {
      'ip': self.ip,
      'port': self.port,
      'username': self.username,
      'password': self.password,
      'created_at': self.created_at.isoformat(),
      'cookies': self.cookies
    }

  @classmethod
  def from_dict(cls, data):
    proxy = cls(data['ip'], data['port'],
                data.get('username'),
                data.get('password'),
                datetime.fromisoformat(data['created_at']))
    proxy.cookies = data['cookies']
    return proxy