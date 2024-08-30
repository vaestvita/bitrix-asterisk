import configparser
from datetime import datetime

import requests

config = configparser.ConfigParser()
config.read('config.ini')

API_URL_YS = config.get('yeastar', 'api_url')
TOKEN_YS = config.get('yeastar', 'token')


resp = requests.post(f'{API_URL_YS}heartbeat?token={TOKEN_YS}')

print(datetime.now(), resp.json())