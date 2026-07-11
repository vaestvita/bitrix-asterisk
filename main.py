# main.py

import sys
import importlib
import threading
import asyncio
from pprint import pprint
import asterx
import config
import asterisk_info


def async_core_info(core_info_container):
    core_info_container['core_info'] = asyncio.run(asterisk_info.collect_core_info())


def main():
    config.prepare_db()
    engine_name = config.ENGINE
    app_mode = config.APP_MODE
    try:
        engine_module = importlib.import_module(engine_name)
    except ImportError as e:
        sys.exit(f"Failed to import module '{engine_name}': {e}")

    core_info = None
    core_info_res = {}
    t = threading.Thread(target=async_core_info, args=(core_info_res,))
    t.start()
    t.join()  # Дождаться результата
    if app_mode == 'cloud':
        core_info = core_info_res.get('core_info')
        # запуск asterx
        t2 = threading.Thread(target=asterx.run, kwargs={'core_info': core_info})
        t2.start()
    engine_module.run()

if __name__ == '__main__':    
    main()
