import requests
import redis
import time

import configparser

r = redis.Redis(host='localhost', port=6379, db=1)

config = configparser.ConfigParser()
config.read('config.ini')

HOST = config.get('asterisk', 'host')
PORT = config.get('asterisk', 'port')
USER = config.get('asterisk', 'username')
SECRET = config.get('asterisk', 'secret')

def originate(internal, external, call_id):
    payload = {
        'endpoint': f'PJSIP/{internal}',
        'extension': external,
        'callerId': f'{external} <{internal}>',
        'context': 'from-internal',
        'priority': 1,
    }

    resp = requests.post(f'https://{HOST}:{PORT}/ari/channels?api_key={USER}:{SECRET}', json=payload)
    if resp.status_code == 200:
        resp_data = resp.json()
        linked_id = resp_data.get('id')
        if linked_id:
            call_data = r.json().get(linked_id, "$")
            if call_data is None:
                call_data = {
                    'start_time': time.time(),
                    'call_id': call_id,
                    'internal': internal,
                    'click2call': True
                }
                r.json().set(linked_id, "$", call_data)