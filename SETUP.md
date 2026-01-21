# Инструкция по установке и настройке

## Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

Или используйте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Шаг 2: Настройка WordPress

### Создание Application Password

1. Войдите в админ-панель WordPress
2. Перейдите в **Пользователи** → **Ваш профиль**
3. Прокрутите вниз до секции **Пароли приложений** (Application Passwords)
4. Введите имя для пароля (например, "MCP Server")
5. Нажмите **Создать новый пароль приложения**
6. **ВАЖНО**: Скопируйте сгенерированный пароль сразу, он больше не будет показан!

### Проверка REST API

Убедитесь, что WordPress REST API доступен:
- Откройте в браузере: `https://your-site.com/wp-json/wp/v2`
- Должна отобразиться информация о доступных endpoints

## Шаг 3: Настройка переменных окружения

1. Скопируйте файл `config.example.env` в `.env`:
```bash
cp config.example.env .env
```

2. Откройте файл `.env` и заполните:
```
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

**Важно:**
- `WORDPRESS_URL` должен быть полным URL без слеша в конце
- `WORDPRESS_APP_PASSWORD` - это пароль приложения, созданный в WordPress (с пробелами или без)

## Шаг 4: Проверка подключения

Запустите тестовый скрипт:

```bash
python example_usage.py
```

Если все настроено правильно, вы увидите информацию о сайте и список постов.

## Шаг 5: Настройка в ChatGPT

### Вариант 1: Через настройки ChatGPT (Desktop/Web)

1. Откройте настройки ChatGPT
2. Перейдите в **Settings** → **Build** → **MCP Servers** (или **Model Context Protocol**)
3. Нажмите **Add Server** или **Create**
4. Заполните:
   - **Name**: WordPress MCP Server
   - **Command**: `python` (или полный путь: `/usr/bin/python3`)
   - **Args**: `["/полный/путь/к/server.py"]`
   - **Env**: Добавьте переменные окружения или укажите путь к `.env` файлу

### Вариант 2: Через конфигурационный файл

Создайте файл конфигурации MCP (зависит от вашего клиента MCP):

```json
{
  "mcpServers": {
    "wordpress": {
      "command": "python",
      "args": ["/полный/путь/к/server.py"],
      "env": {
        "WORDPRESS_URL": "https://your-site.com",
        "WORDPRESS_USERNAME": "your_username",
        "WORDPRESS_APP_PASSWORD": "your_app_password"
      }
    }
  }
}
```

## Шаг 6: Использование

После настройки вы можете использовать ChatGPT для управления WordPress:

- "Создай новый пост с заголовком 'Привет, мир!'"
- "Покажи мне последние 5 постов"
- "Обнови пост #123, измени заголовок на 'Новый заголовок'"
- "Загрузи изображение по URL https://example.com/image.jpg"
- "Создай новую страницу 'О нас'"

## Устранение проблем

### Ошибка подключения

1. Проверьте, что `WORDPRESS_URL` правильный и доступен
2. Убедитесь, что REST API включен (обычно включен по умолчанию)
3. Проверьте Application Password - он должен быть правильным

### Ошибка аутентификации (401)

1. Проверьте правильность `WORDPRESS_USERNAME`
2. Убедитесь, что Application Password скопирован полностью
3. Попробуйте создать новый Application Password

### Ошибка прав доступа (403)

1. Убедитесь, что пользователь имеет права администратора или редактора
2. Проверьте, что REST API не заблокирован плагинами безопасности

### Сервер не запускается

1. Проверьте, что все зависимости установлены: `pip list`
2. Убедитесь, что Python версии 3.8 или выше
3. Проверьте логи ошибок

## Безопасность

- **Никогда не коммитьте `.env` файл в репозиторий**
- Используйте Application Passwords вместо обычных паролей
- Ограничьте доступ к серверу только доверенным IP-адресам (если возможно)
- Регулярно обновляйте зависимости
- Используйте HTTPS для WordPress сайта

## Дополнительная информация

- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
