import configparser
from datetime import datetime
import redis

import requests

import get_token

config = configparser.ConfigParser()
config.read('config.ini')

API_URL_YS = config.get('yeastar', 'api_url')

r = redis.Redis(host='localhost', port=6379, db=1)

token_ys = r.get('yeastar_token').decode('utf-8')

resp = requests.post(f'{API_URL_YS}heartbeat?token={token_ys}').json()
if resp.get('status') == 'Failed':
    print(datetime.now(), resp)
    new_token = get_token.get_token()
    r.set('yeastar_token', new_token)
    resp = requests.post(f'{API_URL_YS}heartbeat?token={new_token}').json()