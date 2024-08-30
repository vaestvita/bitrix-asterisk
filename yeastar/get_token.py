import configparser
import hashlib
import requests

config = configparser.ConfigParser()
config.read('config.ini')

API_USER_YS = config.get('yeastar', 'api_user')
API_PASS_YS = config.get('yeastar', 'api_pass')
API_URL_YS = config.get('yeastar', 'api_url')

# Конвертация пароля в MD5
md5_hash = hashlib.md5(API_PASS_YS.encode()).hexdigest()

payload = {
    'username': API_USER_YS,
    'password': md5_hash,
    'port': 8000,
    'url': 'yeastar'
}

resp = requests.post(f'{API_URL_YS}login', json=payload)

print(resp.json())
