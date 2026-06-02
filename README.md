# VPN list

Автоматизация для Shadowrocket: репозиторий скачивает IP-списки OpenCCK и
собирает два внешних `RULE-SET` файла.

## Готовые файлы

- `dist/opencck-selected-proxy.list` - выбранные сервисы через VPN.
- `dist/opencck-russia-direct.list` - российские IPv4-сети напрямую, без VPN.

Оба файла имеют формат:

```ini
IP-CIDR,1.2.3.0/24,no-resolve
```

## Источники

- Direct: `https://russia.iplist.opencck.org/?format=text&data=cidr4`
- Proxy: `https://iplist.opencck.org/?format=text&data=cidr4&site=youtube.com&site=aistudio.google.com&site=chatgpt.com&site=claude.ai&site=telegram.org&site=whatsapp.com&site=grok.com&site=instagram.com`

## Как подключить в Shadowrocket

```ini
[Rule]
IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
IP-CIDR,127.0.0.0/8,DIRECT,no-resolve

RULE-SET,https://raw.githubusercontent.com/dzhey-aliev/VPN_list/main/dist/opencck-russia-direct.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/dzhey-aliev/VPN_list/main/dist/opencck-selected-proxy.list,PROXY

FINAL,DIRECT
```

Порядок важен: российский `DIRECT` список стоит выше сервисного `PROXY` списка.
Если один и тот же IP попадет в оба списка, сработает первое совпадение, то есть `DIRECT`.

## Локальный запуск

```powershell
python scripts/generate_shadowrocket_lists.py
```

GitHub Actions запускается каждые 6 часов и вручную через `workflow_dispatch`.
