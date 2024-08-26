from flask import Flask, request, jsonify
import configparser
import asyncio
import threading

import bitrix
import ami_engine
from ami_engine import manager

config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config.get('bitrix', 'token')

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def project_info():
    if request.method == 'GET' or request.method == 'POST':
        info = {
            'App': {
                'Name': 'AMI/ARI integration of Asterisk-based PBX with Bitrix24 CRM',
                'URL': 'https://github.com/vaestvita/bitrix-asterisk'
            },
            'Developer': {
                'Name': 'Anton Gulin',
                'Phone': '+7 705 864 55 43',
                'Mail': 'antgulin@ya.ru'
            }
        }
        return jsonify(info)
  
    
@app.route('/bitrix', methods=['POST'])
async def b24_handler():
    application_token = request.form.get('auth[application_token]')
    if application_token != TOKEN:
        return 'Error', 403
    
    event = request.form.get('event')

    if event == 'ONEXTERNALCALLSTART':
        user_id = request.form.get('data[USER_ID]')
        call_id = request.form.get('data[CALL_ID]')
        external = request.form.get('data[PHONE_NUMBER]')
        internal = bitrix.get_user_phone(user_id)
        if internal:
            await ami_engine.originate(internal, external, call_id)

        return 'ok'
    
    else:
        return 'Not supported event', 400


def run_ami_manager():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        manager.connect(run_forever=True)
    )

if __name__ == '__main__':
    ami_thread = threading.Thread(target=run_ami_manager, daemon=True)
    ami_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=8000, use_reloader=False)