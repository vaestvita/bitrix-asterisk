+ [Включить API ](https://help.yeastar.com/en/s-series-developer/api/enable_api_access_on_pbx.html)
+ Логин и пароль вписать в config.ini секция yeastar
+ endpoint - конечная точка для приема вехуков из АТС (сервер на котором запущена эта интеграция)
+ Запустить файл [get_token](/yeastar/get_token.py), полученный токен будет записан в Redis
+ Настроить задачу cron на запуск каждые 25 мин скрипта [run_heartbeat](/yeastar/run_heartbeat.sh)
+ Запустить [api_client](/yeastar/api_client.py)


```
#config.ini
[yeastar]
api_url = http://192.168.1.10:8088/api/v2.0.0/
api_user = pbx
api_pass = pass
endpoint = https://example.com/yeastar
```