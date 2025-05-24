import logging
import os
from dotenv import load_dotenv


class Config:
    def __init__(self):
        self.port = 7963
        self.proxy_host = ''
        self.proxy_username = ''
        self.proxy_password = ''
        self.bypass_url = ''
        self.max_cookie_number = 10
        self.resolve_timeout = 30
        self.click_x_offset = 0
        self.click_y_offset = 0
        self.user_agent = None

    def load_config(self, env_file_path='config.env'):
        if os.path.exists(env_file_path) is False:
            logging.error("config.env文件不存在，请检查当前目录下是否存在config.env文件")
            exit(1)
        load_dotenv(dotenv_path=env_file_path)
        self.port = int(os.getenv('port'))
        self.proxy_host = os.getenv('proxy_host')
        self.proxy_username = os.getenv('proxy_username')
        self.proxy_password = os.getenv('proxy_password')
        self.bypass_url = os.getenv('bypass_url')
        self.max_cookie_number = int(os.getenv('max_cookie_number'))
        self.resolve_timeout = int(os.getenv('resolve_timeout'))
        self.click_x_offset = int(os.getenv('click_x_offset'))
        self.click_y_offset = int(os.getenv('click_y_offset'))
        self.user_agent = os.getenv('user_agent')


