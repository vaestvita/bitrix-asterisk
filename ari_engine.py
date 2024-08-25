import websocket
import json
import redis
import configparser
from datetime import datetime
import bitrix
import utils
import logging

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

r = redis.Redis(host='localhost', port=6379, db=1)

logging.basicConfig(level=logging.INFO, format='%(message)s', filename='log.txt')
logger = logging.getLogger()

def on_message(wsapp, message):
    event = json.loads(message)
    event_type = event.get('type')
    start_time = event.get('timestamp')
    channel = event.get('channel', {})
    caller = channel.get('caller', {})
    channel_id = channel.get('id')
    dialplan = channel.get('dialplan', {})
    context = dialplan.get('context')

    if LOGGING:
        logger = utils.setup_logger(channel_id)
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
            call_data['internal'] = caller_num
            call_data['external'] = exten
            call_data['type'] = 1

        # Inbound call
        elif context in IN_CONTEXTS:
            call_data['internal'] = DEFAULT_PHONE
            call_data['external'] = caller_num
            call_data['type'] = 2

        call_data['call_id'] = bitrix.register_call(call_data)
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
            dialstatus = event.get('dialstatus')
            caller = event.get('caller', {})
            peer = event.get('peer', {})
            peer_dialplan = peer.get('dialplan', {})
            peer_context = peer_dialplan.get('context')
            peer_number = peer_dialplan.get('exten')
            
            if not dialstatus:
                if call_data['type'] == 2:
                    if peer_context == 'from-queue':
                        r.json().set(channel_id, "$.internal", peer_number)
                    else:
                        r.json().set(channel_id, "$.internal", peer.get('caller', {}).get('number'))
                    
                if SHOW_CARD == 1:
                    if peer_number:
                        bitrix.card_action(call_data[0]['call_id'], peer_number, 'show')
                    connected = caller.get('connected', {})
                    number = connected.get('number')
                    if number:
                        bitrix.card_action(call_data[0]['call_id'], number, 'hide')
            
            elif dialstatus == 'ANSWER':
                r.json().set(channel_id, "$.status", 200)
                if peer_context == 'from-queue':
                    number = caller.get('connected', {}).get('number')
                    if number:
                        r.json().set(channel_id, "$.internal", number)
                    else:
                        dialstring = event.get('dialstring', '')
                        r.json().set(channel_id, "$.internal", dialstring.split('/')[1].split('@')[0])
                elif peer_context in LOC_CONTEXTS:
                    r.json().set(channel_id, "$.internal", peer.get('caller', {}).get('number'))

    
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

            resp = bitrix.finish_call(call_data)
            if resp.status_code == 200:
                r.json().delete(channel_id, "$")


wsapp = websocket.WebSocketApp(f"{WS_TYPE}://{HOST}:{PORT}/ari/events?api_key={USER}:{SECRET}&app=thoth&subscribeAll=true",
                               on_message=on_message)

wsapp.run_forever() 