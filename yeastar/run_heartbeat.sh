#!/bin/bash
# Для продления токена запускается каждые 25 мин в cron пользователя bitrix
# https://help.yeastar.com/en/s-series-developer-v2/api-v2/heartbeat.html

cd /home/bitrix/bitrix-asterisk || exit

/home/bitrix/bitrix-asterisk/.venv/bin/python /home/bitrix/bitrix-asterisk/heartbeat.py