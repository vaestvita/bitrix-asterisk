import os
import requests
import configparser
import base64

config = configparser.ConfigParser()
config.read('config.ini')

# Подключение к битрикс
B24_URL = config.get('bitrix', 'url')
CRM_CREATE = config.get('bitrix', 'crm_create')
SHOW_CARD = config.get('bitrix', 'show_card')
DEFAULT_PHONE = config.get('bitrix', 'default_phone')
RECORD_URL = config.get('asterisk', 'records_url')
RECORD_USER = config.get('asterisk', 'record_user')
RECORD_PASS = config.get('asterisk', 'record_pass')

def register_call(call_data: dict):
    payload = {
        'USER_PHONE_INNER': call_data['internal'],
        'PHONE_NUMBER': call_data['external'],
        'CRM_CREATE': CRM_CREATE,
        'SHOW': SHOW_CARD,
        'TYPE': call_data['type']
    }

    resp = requests.post(f'{B24_URL}telephony.externalcall.register', json=payload)
    # print(resp.json())
    if resp.status_code == 200:
        result = resp.json()['result']

        return result['CALL_ID']
    else:
        return None


def finish_call(call_data: dict):
    payload = {
        'CALL_ID': call_data['call_id'],
        'USER_PHONE_INNER': call_data['internal'],
        'DURATION': call_data['duration'],
        'STATUS_CODE': call_data['status']
    }

    resp = requests.post(f'{B24_URL}telephony.externalcall.finish', json=payload)

    if resp.status_code == 200:
        if call_data['status'] == 200 and call_data.get('file_path'):
            file_data = requests.get(f'{RECORD_URL}{call_data["file_path"]}', auth=(RECORD_USER, RECORD_PASS))
            if file_data.status_code == 200:
                file_content = file_data.content
                file_base64 = base64.b64encode(file_content).decode('utf-8')

                payload = {
                    'CALL_ID': call_data['call_id'],
                    'FILENAME': os.path.basename(call_data['file_path']),
                    'FILE_CONTENT': file_base64
                }
                upload_file = requests.post(f'{B24_URL}telephony.externalCall.attachRecord', json=payload)
                # print(upload_file.json())
    return resp



def get_user_id(user_phone):
    payload = {
        'FILTER': {
            'UF_PHONE_INNER': user_phone
        }
    }

    resp = requests.post(f'{B24_URL}user.get', json=payload)
    if resp.status_code == 200:
        user_data = resp.json().get('result', {})
        return user_data[0].get('ID')
    

def get_user_phone(user_id):
    payload = {
        'ID': user_id
    }
    resp = requests.post(f'{B24_URL}user.get', json=payload)
    if resp.status_code == 200:
        user_data = resp.json().get('result', {})
        return user_data[0].get('UF_PHONE_INNER')


def card_action(call_id, user_phone, action):
    user_id = get_user_id(user_phone)
    if user_id:
        payload = {
            'CALL_ID': call_id,
            'USER_ID': user_id,
        }
        requests.post(f'{B24_URL}telephony.externalcall.{action}', json=payload)