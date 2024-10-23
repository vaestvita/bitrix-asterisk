import configparser
import hashlib
import requests
import redis
# Коннект к Redis
r = redis.Redis(host='localhost', port=6379, db=1)

def get_token():
    # Чтение конфигурации
    config = configparser.ConfigParser()
    config.read('config.ini')

    API_USER = config.get('yeastar', 'api_user')
    API_PASS = config.get('yeastar', 'api_pass')
    API_URL = config.get('yeastar', 'api_url')
    API_ENDPOINT = config.get('yeastar', 'api_url')


    # Конвертация пароля в MD5
    md5_hash = hashlib.md5(API_PASS.encode()).hexdigest()

    # Подготовка payload
    payload = {
        'username': API_USER,
        'password': md5_hash,
        'urltag': 1,
        'url': API_ENDPOINT
    }

    # Выполнение POST-запроса
    resp = requests.post(f'{API_URL}login', json=payload).json()

    if resp.get('status') == 'Success':
        token = resp.get('token')

        # Запись токена в Redis
        r.set('yeastar_token', token)

        return token
    else:
        return None

if __name__ == '__main__':
    # Получение и вывод токена
    token = get_token()
    r.set('yeastar_token', token)
    print(f"Token: {token}")
