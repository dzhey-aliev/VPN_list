# VPN list

Автоматизация для Shadowrocket: репозиторий скачивает списки OpenCCK и
собирает внешние `RULE-SET` файлы для маршрутизации DIRECT/PROXY.

## Готовые файлы

Комбинированные файлы для подключения в Shadowrocket:

- `dist/opencck-russia-direct.list` - российские домены, IPv4 и IPv6 напрямую.
- `dist/opencck-selected-proxy.list` - выбранные сервисы через VPN.

Отдельные файлы по типам данных:

- `dist/opencck-russia-direct-domains.list`
- `dist/opencck-russia-direct-cidr4.list`
- `dist/opencck-russia-direct-cidr6.list`
- `dist/opencck-selected-proxy-domains.list`
- `dist/opencck-selected-proxy-cidr4.list`
- `dist/opencck-selected-proxy-cidr6.list`

Форматы правил:

```ini
DOMAIN-SUFFIX,example.com
IP-CIDR,1.2.3.0/24,no-resolve
IP-CIDR6,2001:db8::/32,no-resolve
```

## Источники

DIRECT:

- `https://russia.iplist.opencck.org/?format=text&data=domains&wildcard=1`
- `https://russia.iplist.opencck.org/?format=text&data=cidr4`
- `https://russia.iplist.opencck.org/?format=text&data=cidr6`

PROXY:

- `https://iplist.opencck.org/?format=text&data=domains&wildcard=1&site=youtube.com&site=aistudio.google.com&site=chatgpt.com&site=claude.ai&site=telegram.org&site=whatsapp.com&site=grok.com&site=instagram.com`
- `https://iplist.opencck.org/?format=text&data=cidr4&site=youtube.com&site=aistudio.google.com&site=chatgpt.com&site=claude.ai&site=telegram.org&site=whatsapp.com&site=grok.com&site=instagram.com`
- `https://iplist.opencck.org/?format=text&data=cidr6&site=youtube.com&site=aistudio.google.com&site=chatgpt.com&site=claude.ai&site=telegram.org&site=whatsapp.com&site=grok.com&site=instagram.com`

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
Если один и тот же домен или IP попадет в оба списка, сработает первое совпадение,
то есть `DIRECT`.

## Локальный запуск

```powershell
python scripts/generate_shadowrocket_lists.py
```

GitHub Actions запускается каждые 6 часов и вручную через `workflow_dispatch`.
