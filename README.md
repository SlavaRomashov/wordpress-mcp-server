# WordPress MCP Server

Полнофункциональный MCP (Model Context Protocol) сервер для управления WordPress через ChatGPT и другие AI-ассистенты.

## Возможности

- ✅ Управление постами (создание, редактирование, удаление, получение)
- ✅ Управление страницами
- ✅ Управление пользователями
- ✅ Управление медиафайлами
- ✅ Управление комментариями
- ✅ Управление категориями и тегами
- ✅ Поиск контента
- ✅ Получение информации о сайте
- ✅ Поддержка Cloudflare Tunnel для безопасного подключения

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/YOUR_USERNAME/wordpress-mcp-server.git
cd wordpress-mcp-server
```

Или скачайте ZIP архив проекта и распакуйте его.

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Скопируйте файл `config.example.env` в `.env`:
```bash
cp config.example.env .env
```

4. Настройте переменные окружения в файле `.env`:
```
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=your_application_password
```

## Получение Application Password в WordPress

1. Войдите в админ-панель WordPress
2. Перейдите в **Пользователи** → **Ваш профиль**
3. Прокрутите вниз до секции **Пароли приложений**
4. Создайте новый пароль приложения, указав имя (например, "MCP Server")
5. Скопируйте сгенерированный пароль и используйте его в `.env` файле

## Запуск сервера

```bash
python server.py
```

Или используйте `mcp` команду:
```bash
mcp run server.py
```

## Настройка в ChatGPT

### Стандартное подключение (локально)

1. Откройте настройки ChatGPT
2. Перейдите в **Settings** → **Build** → **MCP Servers**
3. Добавьте новый сервер:
   - **Name**: WordPress MCP Server
   - **Command**: `python` (или `python3`)
   - **Args**: `["/полный/путь/к/server.py"]`
   - **Env**: Укажите переменные окружения или используйте `.env` файл

### Подключение через Cloudflare Tunnel

Если ChatGPT работает на удаленном сервере или вы хотите использовать Cloudflare Tunnel для дополнительной безопасности:

1. Следуйте инструкциям в [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)
2. Настройте Cloudflare Tunnel согласно документации
3. Используйте стандартную конфигурацию MCP в ChatGPT (туннель работает прозрачно)

**Примечание**: MCP серверы обычно работают через stdio (stdin/stdout), поэтому Cloudflare Tunnel настраивается отдельно для обеспечения безопасного соединения между ChatGPT и вашим сервером.

## Доступные инструменты

### Посты
- `wp_create_post` - Создать новый пост
- `wp_get_post` - Получить пост по ID
- `wp_list_posts` - Получить список постов
- `wp_update_post` - Обновить пост
- `wp_delete_post` - Удалить пост

### Страницы
- `wp_create_page` - Создать новую страницу
- `wp_get_page` - Получить страницу по ID
- `wp_list_pages` - Получить список страниц
- `wp_update_page` - Обновить страницу
- `wp_delete_page` - Удалить страницу

### Пользователи
- `wp_get_user` - Получить пользователя по ID
- `wp_list_users` - Получить список пользователей
- `wp_create_user` - Создать нового пользователя
- `wp_update_user` - Обновить пользователя

### Медиа
- `wp_upload_media` - Загрузить медиафайл
- `wp_get_media` - Получить медиафайл по ID
- `wp_list_media` - Получить список медиафайлов

### Комментарии
- `wp_get_comment` - Получить комментарий по ID
- `wp_list_comments` - Получить список комментариев
- `wp_create_comment` - Создать комментарий
- `wp_update_comment` - Обновить комментарий
- `wp_delete_comment` - Удалить комментарий

### Категории
- `wp_list_categories` - Получить список категорий
- `wp_get_category` - Получить категорию по ID
- `wp_create_category` - Создать новую категорию

### Теги
- `wp_list_tags` - Получить список тегов
- `wp_get_tag` - Получить тег по ID
- `wp_create_tag` - Создать новый тег

### Поиск
- `wp_search` - Выполнить поиск по сайту

### Информация о сайте
- `wp_get_site_info` - Получить информацию о сайте

## Примеры использования

### Создание поста
```
Создай новый пост с заголовком "Привет, мир!" и содержимым "Это мой первый пост через MCP"
```

### Получение списка постов
```
Покажи мне последние 10 постов
```

### Загрузка медиа
```
Загрузи изображение по URL https://example.com/image.jpg с заголовком "Мое изображение"
```

## Cloudflare Tunnel

Для безопасного подключения ChatGPT к локальному MCP серверу через Cloudflare Tunnel:

1. См. подробные инструкции в [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)
2. Используйте скрипт `start_with_tunnel.sh` для запуска с туннелем
3. Настройте DNS запись в Cloudflare панели

**Быстрый старт с Cloudflare Tunnel:**
```bash
# 1. Установите cloudflared
brew install cloudflare/cloudflare/cloudflared  # macOS
# или
sudo snap install cloudflared  # Linux

# 2. Авторизуйтесь
cloudflared tunnel login

# 3. Создайте туннель
cloudflared tunnel create wordpress-mcp

# 4. Настройте DNS
cloudflared tunnel route dns wordpress-mcp your-mcp-server.yourdomain.com

# 5. Запустите туннель
cloudflared tunnel run wordpress-mcp
```

## Безопасность

- Никогда не коммитьте файл `.env` в репозиторий
- Используйте Application Passwords вместо обычных паролей
- Используйте Cloudflare Tunnel для безопасного подключения извне
- Ограничьте доступ к серверу только доверенным IP-адресам (если возможно)
- Регулярно обновляйте зависимости
- Храните credentials файлы Cloudflare Tunnel в безопасном месте

## Лицензия

MIT

## Поддержка

При возникновении проблем создайте issue в репозитории проекта.
