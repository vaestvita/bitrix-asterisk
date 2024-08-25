# Bitrix AMI/ARI 

Протестировано с Asterisk v. 16, 18, 20 (FreePBX) - если названия используемых в фильтрах контекстов, отличаются от используемых в вашей системе - замените их.

Скрипт позволяет отправлять историю звонков и файлы записей из Asterisk (FreePBX) в Битрикс24

Работает с AMI событиями [CEL](/ami_cel.py) или [ARI](/ari_engine.py)

### Установка 

Для временного хранения информации о звонках используется [RedisJSON](https://github.com/RedisJSON/RedisJSON) 
```
docker run -p 6379:6379 --name redis-stack redis/redis-stack:latest
```

```
cd /opt
git clone https://github.com/vaestvita/bitrix-asterisk.git
cd bitrix-asterisk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp examples/config.ini config.ini
nano config.ini
```
 
### Заполнить данные в [config.ini](examples/config.ini)

Описание параметров [bitrix]
+ [url] - Адрес воходящего вебхука. Интеграции > Rest API > Другое > Входящий вебхук (Необходимые права: crm, user, telephony)
+ [crm_create] - Создавать или нет сущность CRM (1/0)
+ [show_card] - Показывать или нет карточку клиента (1/0)
+ [default_phone] - Внутренний номер по умолчанию (должен быть указан в настройках телефонии - пользователи телефонии).

Описание параметров [asterisk]
+ [ws_type] - wss/ws - требуестя при подключении к ARI
+ [host] - адрес ATC (example.com)
+ [port] - AMI/ARI порт
+ [username] - AMI/ARI пользователь
+ [secret] - AMI/ARI пароль
+ [records_url] - url с записями звонков с HTTP Basic Auth (https://example.com/monitor/). Пример конфига [Apache](examples/monitor.conf)
+ [record_user] - логин Basic Auth
+ [record_pass] - пароль Basic Auth
+ [loc_count] - количество знаков внутренних номеров. Если поставить 0, то внутренние звонки тоже будет передаваться в битрикс
+ [loc_contexts] - список контекстов внутренних (исходящие) вызовов. По умолчанию "from-internal"
+ [out_contexts] - список контекстов внешних вызовов. По умолчанию "from-pstn"
+ [logging] - True/False - включить/отключить запись получаемых событий в файл.

## Запуск интеграции

```
ARI - python ari_engine.py
AMI - python ami_cel.py
```

Пример конфигурации [systemd](/examples/b24_integration.service) для автоматического запуска