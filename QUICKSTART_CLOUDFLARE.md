# Быстрый старт с Cloudflare Tunnel

## За 10 минут настроить WordPress MCP Server через Cloudflare Tunnel

### Шаг 1: Установка зависимостей (2 минуты)

```bash
# Установите Python зависимости
pip install -r requirements.txt

# Установите Cloudflare Tunnel
# macOS
brew install cloudflare/cloudflare/cloudflared

# Linux
sudo snap install cloudflared
# или
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Шаг 2: Настройка WordPress (2 минуты)

1. Войдите в WordPress админ-панель
2. Перейдите: **Пользователи** → **Ваш профиль** → **Пароли приложений**
3. Создайте новый пароль (например, "MCP Server")
4. Скопируйте пароль

### Шаг 3: Настройка .env (1 минута)

```bash
cp config.example.env .env
```

Отредактируйте `.env`:
```
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

### Шаг 4: Настройка Cloudflare Tunnel (3 минуты)

```bash
# 1. Авторизуйтесь в Cloudflare
cloudflared tunnel login

# 2. Создайте туннель
cloudflared tunnel create wordpress-mcp

# 3. Настройте DNS (замените yourdomain.com на ваш домен)
cloudflared tunnel route dns wordpress-mcp mcp.yourdomain.com

# 4. Получите Tunnel ID
cloudflared tunnel list
```

### Шаг 5: Конфигурация туннеля (1 минута)

Отредактируйте `cloudflare-tunnel-config.yaml`:

```yaml
tunnel: YOUR_TUNNEL_ID  # Замените на ваш Tunnel ID
credentials-file: /path/to/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: mcp.yourdomain.com
    service: stdio  # Для MCP через stdio
  - service: http_status:404
```

### Шаг 6: Запуск (1 минута)

```bash
# Запустите туннель в одном терминале
cloudflared tunnel run wordpress-mcp

# В другом терминале запустите MCP сервер
python3 server.py
```

### Шаг 7: Настройка ChatGPT

В настройках ChatGPT:
- **Settings** → **Build** → **MCP Servers**
- **Add Server**:
  - Name: `WordPress`
  - Command: `python3`
  - Args: `["/полный/путь/к/server.py"]`
  - Env: Добавьте переменные из `.env`

**Готово!** 🎉

## Альтернативный способ: Использование скрипта

```bash
# Сделайте скрипт исполняемым
chmod +x start_with_tunnel.sh

# Запустите
./start_with_tunnel.sh
```

## Проверка работы

Попробуйте команды в ChatGPT:
- "Покажи информацию о WordPress сайте"
- "Создай новый пост с заголовком 'Тест'"
- "Покажи последние 5 постов"

## Устранение проблем

### Туннель не подключается
```bash
# Проверьте статус
cloudflared tunnel info wordpress-mcp

# Проверьте логи
cloudflared tunnel run wordpress-mcp --loglevel debug
```

### DNS не работает
- Убедитесь, что DNS запись создана в Cloudflare
- Проверьте, что запись проксируется (оранжевое облако)
- Подождите несколько минут для распространения DNS

### Ошибки подключения к WordPress
- Проверьте `.env` файл
- Убедитесь, что Application Password правильный
- Проверьте доступность WordPress REST API: `https://your-site.com/wp-json/wp/v2`

## Дополнительная информация

- Полная документация: [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)
- Основная документация: [README.md](README.md)
- Быстрый старт без туннеля: [QUICKSTART.md](QUICKSTART.md)
