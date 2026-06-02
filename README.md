# VPN list

Автоматизация для Shadowrocket: репозиторий скачивает списки Antifilter и
собирает два внешних `RULE-SET` файла.

## Готовые файлы

- `dist/antifilter-domains.list` - домены в формате `DOMAIN-SUFFIX,<domain>`.
- `dist/antifilter-community-ip.list` - IP-сети в формате `IP-CIDR,<cidr>,no-resolve`.

## Как подключить в Shadowrocket

После публикации репозитория на GitHub замени `<user>` и `<repo>` на свои:

```ini
[Rule]
RULE-SET,https://raw.githubusercontent.com/<user>/<repo>/main/dist/antifilter-domains.list,PROXY
RULE-SET,https://raw.githubusercontent.com/<user>/<repo>/main/dist/antifilter-community-ip.list,PROXY

IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
IP-CIDR,172.16.0.0/12,DIRECT,no-resolve

FINAL,DIRECT
```

## Локальный запуск

```powershell
python scripts/generate_shadowrocket_lists.py
```

GitHub Actions запускается каждые 6 часов и вручную через `workflow_dispatch`.
