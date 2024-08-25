import time
import re
import json
import configparser
import logging

import redis

from panoramisk import Manager, Message

import bitrix
import utils

config = configparser.ConfigParser()
config.read('config.ini')

HOST = config.get('asterisk', 'host')
PORT = config.get('asterisk', 'port')
USER = config.get('asterisk', 'username')
SECRET = config.get('asterisk', 'secret')
LOC_CONTEXTS = config.get('asterisk', 'loc_contexts')
IN_CONTEXTS = config.get('asterisk', 'out_contexts')
DEFAULT_PHONE = config.get('bitrix', 'default_phone')
LOCAL_COUNT = config.getint('asterisk', 'loc_count')
LOGGING = config.getboolean('asterisk', 'logging')
SHOW_CARD = config.getint('bitrix', 'show_card')

CONTEXTS = IN_CONTEXTS + LOC_CONTEXTS

STATUSES = {
    '3': 503,
    '17': 486,
    '19': 480,
    '20': 480,
    '21': 403,
    '31': 200,
    '34': 404,
    '38': 503,
    '127': 603,
}

r = redis.Redis(host='localhost', port=6379, db=1)

logging.basicConfig(level=logging.INFO, format='%(message)s', filename='log.txt')
logger = logging.getLogger()


manager = Manager(
    host=HOST,
    port=PORT,
    username=USER,
    secret=SECRET,
    ping_delay=1,  # Delay after start
    ping_interval=3,  # Periodically ping AMI (dead or alive)
)

@manager.register_event('CEL')
async def ami_callback(mngr: Manager, message: Message):
    linked_id = message.Linkedid
    context = message.Context
    event = message.EventName
    app = message.Application

    if LOGGING:
        logger = utils.setup_logger(linked_id)
        logger.info(message)

    call_data = r.json().get(linked_id, "$")

    if event == 'CHAN_START':
        if call_data is None:
            call_data = {
                'start_time': time.time()
            }

            caller = message.CallerIDnum
            exten = message.Exten

            if exten == "s" or "*" in exten:
                return

            # Outbound call
            if context in LOC_CONTEXTS and len(exten) > LOCAL_COUNT:
                call_data.update({
                    'internal': caller,
                    'external': exten,
                    'type': 1
                })
            # Inbound call
            elif context in IN_CONTEXTS:
                call_data.update({
                    'internal': DEFAULT_PHONE,
                    'external': caller,
                    'type': 2
                })
            # Other contexts
            else:
                return
            
            call_data['call_id'] = bitrix.register_call(call_data)
            r.json().set(linked_id, "$", call_data)

    elif event == 'APP_START':
        if call_data:
            if app == 'MixMonitor':
                r.json().set(linked_id, "$.file_path", message.AppData.split(',')[0])
            elif app == 'Dial' and SHOW_CARD == 1:
                phone = re.split('[-@]', message.Channel.split('/')[1])[0]
                bitrix.card_action(call_data[0]['call_id'], phone, 'show')

    elif event == 'APP_END':
        if call_data:
            if app == 'Dial' and SHOW_CARD == 1:
                phone = re.split('[-@]', message.Channel.split('/')[1])[0]
                bitrix.card_action(call_data[0]['call_id'], phone, 'hide')

    elif event == 'PICKUP':
        if call_data:
            extra = json.loads(message.Extra)
            channel = extra.get('pickup_channel')
            r.json().set(linked_id, "$.internal", channel.split('/')[1].split('-')[0])
            r.json().set(linked_id, "$.status", 200)

    elif event == 'ANSWER':
        if call_data:
            if context in CONTEXTS:
                r.json().set(linked_id, "$.status", 200)
                if call_data[0]['type'] == 2:
                    r.json().set(linked_id, "$.internal", message.CallerIDnum)
            elif context in ['ext-queues']:
                r.json().set(linked_id, "$.queue", True)

    elif event == 'BLINDTRANSFER':
        if call_data:
            extra = json.loads(message.Extra)
            r.json().set(linked_id, "$.internal", extra.get('extension'))

    elif event == 'ATTENDEDTRANSFER':
        if call_data:
            extra = json.loads(message.Extra)
            target_internal = extra.get('transfer_target_channel_name')
            r.json().set(linked_id, "$.internal", target_internal.split('/')[1].split('@')[0])

    elif event == 'HANGUP':
        if call_data and call_data[0].get('status') != 200:
            if context in LOC_CONTEXTS:
                extra = json.loads(message.Extra)
                dialstatus = STATUSES.get(str(extra.get('hangupcause')), 304)
                r.json().set(linked_id, "$.status", dialstatus)
                if call_data[0]['type'] == 2:
                    r.json().set(linked_id, "$.internal", message.CallerIDnum)

    elif event == 'LINKEDID_END':
        if call_data:
            call_data = call_data[0]
            call_data['duration'] = round(time.time() - call_data['start_time'])
            resp = bitrix.finish_call(call_data)
            if resp.status_code == 200:
                r.json().delete(linked_id, "$")


if __name__ == '__main__':
    manager.connect(run_forever=True)