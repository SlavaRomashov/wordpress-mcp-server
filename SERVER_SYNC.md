# Синхронизация сервера с GitHub

## Автоматическая синхронизация

### Вариант 1: Использование скрипта sync_server.sh

```bash
./sync_server.sh
```

**Требования:**
- SSH ключи должны быть настроены для доступа к серверу
- Или используйте SSH агент с паролем

### Вариант 2: Ручная синхронизация через SSH

Выполните команды на сервере:

```bash
# Подключитесь к серверу
ssh root@85.198.103.185

# Затем выполните команды синхронизации
cd /opt/wordpress-mcp-server
git fetch origin
git reset --hard origin/main
python3 -m pip install -r requirements.txt --quiet

# Перезапустите сервис если запущен
systemctl restart wordpress-mcp-server
```

### Вариант 3: Использование скрипта на сервере

```bash
# Загрузите скрипт на сервер
scp sync_server_manual.sh root@85.198.103.185:/tmp/

# Подключитесь и выполните
ssh root@85.198.103.185
chmod +x /tmp/sync_server_manual.sh
/tmp/sync_server_manual.sh
```

## Быстрая команда для синхронизации

Одной командой через SSH:

```bash
ssh root@85.198.103.185 "cd /opt/wordpress-mcp-server && git fetch origin && git reset --hard origin/main && python3 -m pip install -r requirements.txt --quiet && systemctl daemon-reload && systemctl restart wordpress-mcp-server 2>/dev/null || echo 'Сервис не запущен'"
```

## Настройка SSH ключей (если еще не настроено)

```bash
# Генерация SSH ключа (если еще нет)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Копирование ключа на сервер
ssh-copy-id root@85.198.103.185

# Или вручную
cat ~/.ssh/id_ed25519.pub | ssh root@85.198.103.185 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

## Проверка синхронизации

После синхронизации проверьте:

```bash
# Версия на сервере
ssh root@85.198.103.185 "cd /opt/wordpress-mcp-server && git log -1 --oneline"

# Статус сервиса
ssh root@85.198.103.185 "systemctl status wordpress-mcp-server"

# Логи
ssh root@85.198.103.185 "journalctl -u wordpress-mcp-server -n 50"
```

## Автоматизация через cron

Для автоматической синхронизации каждые 5 минут:

```bash
# На сервере выполните:
crontab -e

# Добавьте строку:
*/5 * * * * cd /opt/wordpress-mcp-server && git fetch origin && git reset --hard origin/main && python3 -m pip install -r requirements.txt --quiet >/dev/null 2>&1 && systemctl restart wordpress-mcp-server >/dev/null 2>&1
```

## Структура на сервере

```
/opt/wordpress-mcp-server/
├── server.py
├── requirements.txt
├── .env (ваши настройки)
├── config.example.env
└── ... (остальные файлы)

/etc/systemd/system/wordpress-mcp-server.service
```

## Управление сервисом

```bash
# Запуск
ssh root@85.198.103.185 "systemctl start wordpress-mcp-server"

# Остановка
ssh root@85.198.103.185 "systemctl stop wordpress-mcp-server"

# Перезапуск
ssh root@85.198.103.185 "systemctl restart wordpress-mcp-server"

# Статус
ssh root@85.198.103.185 "systemctl status wordpress-mcp-server"

# Логи
ssh root@85.198.103.185 "journalctl -u wordpress-mcp-server -f"

# Автозапуск при загрузке
ssh root@85.198.103.185 "systemctl enable wordpress-mcp-server"
```

## Устранение проблем

### Ошибка подключения SSH

1. Проверьте доступность сервера: `ping 85.198.103.185`
2. Проверьте SSH: `ssh -v root@85.198.103.185`
3. Убедитесь, что порт 22 открыт

### Ошибка git pull

```bash
# На сервере
cd /opt/wordpress-mcp-server
git fetch origin
git reset --hard origin/main
```

### Ошибка установки зависимостей

```bash
# На сервере
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### Сервис не запускается

```bash
# Проверьте логи
ssh root@85.198.103.185 "journalctl -u wordpress-mcp-server -n 100"

# Проверьте .env файл
ssh root@85.198.103.185 "cat /opt/wordpress-mcp-server/.env"

# Запустите вручную для отладки
ssh root@85.198.103.185 "cd /opt/wordpress-mcp-server && python3 server.py"
```
