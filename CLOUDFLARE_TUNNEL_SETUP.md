# Настройка Cloudflare Tunnel для WordPress MCP Server

Это руководство поможет вам настроить Cloudflare Tunnel для безопасного подключения ChatGPT к вашему локальному WordPress MCP серверу.

## Что такое Cloudflare Tunnel?

Cloudflare Tunnel (cloudflared) создает безопасное соединение между вашим локальным сервером и ChatGPT, не требуя открытия портов в файрволе или настройки переадресации портов на роутере.

## Преимущества

- ✅ Безопасность: не нужно открывать порты
- ✅ Простота: не требуется настройка роутера
- ✅ Надежность: автоматическое переподключение
- ✅ Бесплатно: Cloudflare Tunnel бесплатен для личного использования

## Шаг 1: Установка cloudflared

### macOS
```bash
brew install cloudflare/cloudflare/cloudflared
```

### Linux
```bash
# Ubuntu/Debian
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Или через snap
sudo snap install cloudflared
```

### Windows
Скачайте установщик с [официального сайта Cloudflare](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)

### Проверка установки
```bash
cloudflared --version
```

## Шаг 2: Аутентификация в Cloudflare

```bash
cloudflared tunnel login
```

Это откроет браузер для авторизации. Выберите домен, который хотите использовать.

## Шаг 3: Создание туннеля

```bash
cloudflared tunnel create wordpress-mcp
```

Сохраните выведенный Tunnel ID - он понадобится для конфигурации.

## Шаг 4: Настройка DNS записи

### Вариант 1: Автоматическая настройка (рекомендуется)
```bash
cloudflared tunnel route dns wordpress-mcp your-mcp-server.yourdomain.com
```

### Вариант 2: Ручная настройка
1. Перейдите в панель Cloudflare → DNS
2. Добавьте CNAME запись:
   - **Name**: `your-mcp-server` (или любое поддомен)
   - **Target**: `YOUR_TUNNEL_ID.cfargotunnel.com`
   - **Proxy**: Включен (оранжевое облако)

## Шаг 5: Настройка конфигурации туннеля

### Для MCP через stdio (рекомендуется)

MCP серверы обычно работают через stdio (stdin/stdout), поэтому Cloudflare Tunnel должен проксировать stdio соединение. Однако, для этого нужна специальная настройка.

### Альтернативный подход: HTTP сервер

Если ваш MCP клиент поддерживает HTTP, можно создать HTTP обертку:

1. Создайте файл `cloudflare-tunnel-config.yaml`:
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /path/to/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: your-mcp-server.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

2. Обновите `server.py` для поддержки HTTP режима (если нужно)

## Шаг 6: Запуск туннеля

### Ручной запуск
```bash
cloudflared tunnel --config cloudflare-tunnel-config.yaml run wordpress-mcp
```

### Запуск как служба (Linux/macOS)

```bash
# Установка службы
sudo cloudflared service install

# Запуск туннеля
cloudflared tunnel run wordpress-mcp
```

### Запуск как служба (Windows)

```powershell
# Установка службы
cloudflared.exe service install

# Запуск туннеля
cloudflared.exe tunnel run wordpress-mcp
```

## Шаг 7: Настройка ChatGPT для работы через Cloudflare Tunnel

### Вариант 1: Прямое подключение через stdio (стандартный MCP)

ChatGPT обычно подключается к MCP серверам через stdio, поэтому Cloudflare Tunnel не требуется напрямую. Туннель нужен только если:

1. ChatGPT работает на удаленном сервере
2. Вы хотите использовать HTTP-интерфейс MCP

### Вариант 2: Использование HTTP-интерфейса

Если ваш MCP клиент поддерживает HTTP:

1. В настройках ChatGPT укажите URL туннеля:
   ```
   https://your-mcp-server.yourdomain.com
   ```

2. Убедитесь, что сервер доступен через туннель

## Альтернативный подход: Использование локального подключения

Если ChatGPT работает локально на той же машине, Cloudflare Tunnel не нужен. Просто используйте стандартную настройку MCP:

```json
{
  "mcpServers": {
    "wordpress": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "WORDPRESS_URL": "https://your-site.com",
        "WORDPRESS_USERNAME": "your_username",
        "WORDPRESS_APP_PASSWORD": "your_app_password"
      }
    }
  }
}
```

## Когда нужен Cloudflare Tunnel?

Cloudflare Tunnel необходим, если:

1. ✅ ChatGPT работает на удаленном сервере или в облаке
2. ✅ Вы хотите подключиться к локальному MCP серверу извне
3. ✅ У вас нет возможности настроить переадресацию портов
4. ✅ Вы хотите дополнительный уровень безопасности

## Устранение проблем

### Туннель не подключается
```bash
# Проверьте статус
cloudflared tunnel info wordpress-mcp

# Проверьте логи
cloudflared tunnel run wordpress-mcp --loglevel debug
```

### DNS не разрешается
- Убедитесь, что DNS запись создана и проксируется (оранжевое облако)
- Подождите несколько минут для распространения DNS

### Ошибки аутентификации
```bash
# Переавторизуйтесь
cloudflared tunnel login
```

## Безопасность

- ✅ Используйте HTTPS для WordPress сайта
- ✅ Храните credentials файл в безопасном месте
- ✅ Не коммитьте конфигурационные файлы с секретами в Git
- ✅ Регулярно обновляйте cloudflared

## Дополнительные ресурсы

- [Официальная документация Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Cloudflare Tunnel GitHub](https://github.com/cloudflare/cloudflared)

## Пример полной настройки

```bash
# 1. Установка
brew install cloudflare/cloudflare/cloudflared

# 2. Авторизация
cloudflared tunnel login

# 3. Создание туннеля
cloudflared tunnel create wordpress-mcp

# 4. Настройка DNS
cloudflared tunnel route dns wordpress-mcp mcp.yourdomain.com

# 5. Запуск туннеля
cloudflared tunnel run wordpress-mcp
```

После этого ваш MCP сервер будет доступен через `https://mcp.yourdomain.com`
