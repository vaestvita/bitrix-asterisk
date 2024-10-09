#!/bin/bash
# Для продления токена запускается каждые 25 мин в cron пользователя bitrix
# https://help.yeastar.com/en/s-series-developer-v2/api-v2/heartbeat.html

cd /opt/bitrix-asterisk || exit

/opt/bitrix-asterisk/.venv/bin/python /opt/bitrix-asterisk/heartbeat.py
