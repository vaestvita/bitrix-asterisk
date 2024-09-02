import sys
import re
import os
import websocket
import time
import json
import redis
import configparser
from datetime import datetime
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bitrix import *
from utils import setup_logger

websocket.enableTrace(False)

config = configparser.ConfigParser()
config.read('config.ini')

WS_TYPE = config.get('asterisk', 'ws_type')
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


STATUS_CODES = {
    '3': 503,
    '17': 486,
    '19': 480,
    '20': 480,
    '21': 403,
    '31': 200,
    '34': 603,
    '38': 503,
    '127': 603,
}


pattern = r'(?<=/)(\d+)|(?<=sip:)\d+'

r = redis.Redis(host='localhost', port=6379, db=1)

logging.basicConfig(level=logging.INFO, format='%(message)s', filename='log3.txt')
logger = logging.getLogger()

def on_message(ws, message):
    event = json.loads(message)
    event_type = event.get('type')
    start_time = event.get('timestamp')
    channel = event.get('channel', {})
    caller = channel.get('caller', {})
    channel_id = channel.get('id')
    dialplan = channel.get('dialplan', {})
    context = dialplan.get('context')

    if LOGGING:
        logger = setup_logger(channel_id)
        logger.info(message)

    if event_type == 'ChannelCreated':
        caller_num = caller.get('number')
        exten = dialplan['exten']
        
        if exten == "s" or "*" in exten:
            return   
                 
        call_data = {
            "start_time": start_time,
        }

        # Outbound call
        if context in LOC_CONTEXTS:
            call_data.update({
                'internal': caller_num,
                'external': exten,
                'type': 1
            })

        # Inbound call
        elif context in IN_CONTEXTS:
            call_data.update({
                'internal': DEFAULT_PHONE,
                'external': caller_num,
                'type': 2
            })

        call_data['call_id'] = register_call(call_data)
        r.json().set(channel_id, "$", call_data)

    elif event_type == 'ChannelDialplan' and event['dialplan_app'] == 'GotoIf' and context in LOC_CONTEXTS:
        call_data = r.json().get(channel_id, "$")
        if call_data:
            r.json().delete(channel_id, "$")
    
    elif event_type == 'ChannelVarset':
        variable = event.get('variable')
        if variable == 'MIXMONITOR_FILENAME':
            call_data = r.json().get(channel_id, "$")
            if call_data:
                file_path = event.get('value')
                file_path = file_path.replace("/var/spool/asterisk/monitor", "")                 
                r.json().set(channel_id, "$.file_path", file_path)
    
    elif event_type == 'Dial':
        channel_id = event['caller']['id']
        call_data = r.json().get(channel_id, "$")
        
        if call_data:
            call_data = call_data[0]
            dialstatus = event.get('dialstatus')
            dialstring = event.get('dialstring')

            if call_data.get('type') == 2 and SHOW_CARD == 1:
                call_id = call_data.get('call_id')
                if not dialstatus and dialstring:
                    match = re.search(pattern, dialstring)
                    internal = match.group(0)
                    r.json().set(channel_id, "$.internal", internal)
                    card_action(call_id, internal, 'show')
                elif dialstatus in ['NOANSWER', 'BUSY']:
                    peer_name = event.get('peer').get('name')
                    match = re.search(pattern, peer_name)
                    internal = match.group(0)
                    card_action(call_id, internal, 'hide')
            
            if dialstatus == 'ANSWER':
                r.json().set(channel_id, "$.status", 200)

    
    elif event_type == 'BridgeBlindTransfer' and event['result'] == 'Success':
        call_data = r.json().get(channel_id, "$")
        if call_data:
            r.json().delete(channel_id, "$")
            channel_id = event['transferee']['id']
            r.json().set(channel_id, "$", call_data)
            r.json().set(channel_id, "$.internal", event['exten'])
    
    elif event_type == 'ChannelDestroyed':
        end_time = event.get('timestamp')

        call_data = r.json().get(channel_id, "$")
        if call_data:
            call_data = call_data[0]
            start_time = call_data['start_time']
            start_time_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_time_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            call_data['call_duration'] = round((end_time_dt - start_time_dt).total_seconds())
            cause = str(event['cause'])
            call_data['status'] = call_data.get('status', STATUS_CODES.get(cause, 304))

            resp = finish_call(call_data)
            if resp.status_code == 200:
                r.json().delete(channel_id, "$")


def on_error(ws, error):
    print("Error:", error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

def run_websocket():
    while True:
        ws = websocket.WebSocketApp(f"{WS_TYPE}://{HOST}:{PORT}/ari/events?api_key={USER}:{SECRET}&app=thoth&subscribeAll=true",
                                    on_message=on_message,
                                    on_error=on_error)
        ws.on_open = on_open
        ws.run_forever(ping_interval=60, ping_timeout=10)
        print("Reconnecting...")
        time.sleep(1)


if __name__ == '__main__':
    run_websocket()