# Структура проекта WordPress MCP Server

## Файлы проекта

```
wordpress-mcp-server/
├── server.py                 # Основной MCP сервер с всеми инструментами
├── example_usage.py          # Примеры использования функций
├── requirements.txt          # Зависимости Python
├── config.example.env        # Пример конфигурации
├── .gitignore               # Игнорируемые файлы для Git
├── README.md                # Основная документация
├── SETUP.md                 # Подробная инструкция по установке
├── QUICKSTART.md            # Быстрый старт за 5 минут
└── PROJECT_STRUCTURE.md     # Этот файл
```

## Описание файлов

### server.py
Основной файл MCP сервера, содержащий:
- **WordPressClient** - класс для работы с WordPress REST API
- **25+ инструментов (tools)** для управления WordPress:
  - Посты (5 инструментов)
  - Страницы (5 инструментов)
  - Пользователи (4 инструмента)
  - Медиафайлы (3 инструмента)
  - Комментарии (5 инструментов)
  - Информация о сайте (1 инструмент)

### example_usage.py
Демонстрационный скрипт для проверки подключения и тестирования функций.

### requirements.txt
Зависимости проекта:
- `fastmcp` - фреймворк для создания MCP серверов
- `httpx` - HTTP клиент для запросов к WordPress API
- `python-dotenv` - загрузка переменных окружения
- `pydantic` - валидация данных

### config.example.env
Шаблон файла конфигурации с переменными окружения.

## Доступные инструменты

### Управление постами
- `wp_create_post` - Создать пост
- `wp_get_post` - Получить пост
- `wp_list_posts` - Список постов
- `wp_update_post` - Обновить пост
- `wp_delete_post` - Удалить пост

### Управление страницами
- `wp_create_page` - Создать страницу
- `wp_get_page` - Получить страницу
- `wp_list_pages` - Список страниц
- `wp_update_page` - Обновить страницу
- `wp_delete_page` - Удалить страницу

### Управление пользователями
- `wp_get_user` - Получить пользователя
- `wp_list_users` - Список пользователей
- `wp_create_user` - Создать пользователя
- `wp_update_user` - Обновить пользователя

### Управление медиа
- `wp_upload_media` - Загрузить медиафайл
- `wp_get_media` - Получить медиафайл
- `wp_list_media` - Список медиафайлов

### Управление комментариями
- `wp_get_comment` - Получить комментарий
- `wp_list_comments` - Список комментариев
- `wp_create_comment` - Создать комментарий
- `wp_update_comment` - Обновить комментарий
- `wp_delete_comment` - Удалить комментарий

### Информация
- `wp_get_site_info` - Информация о сайте

## Технологии

- **Python 3.8+** - основной язык
- **FastMCP** - фреймворк MCP сервера
- **WordPress REST API** - API для управления WordPress
- **Basic Authentication** - аутентификация через Application Passwords

## Безопасность

- Использование Application Passwords вместо обычных паролей
- Переменные окружения для конфиденциальных данных
- Обработка ошибок и валидация входных данных
- HTTPS поддержка

## Расширение функциональности

Для добавления новых инструментов:
1. Создайте функцию с декоратором `@mcp.tool()`
2. Используйте `get_client()` для получения клиента WordPress
3. Выполните необходимые операции через REST API
4. Верните результат в формате словаря

Пример:
```python
@mcp.tool()
def wp_custom_tool(param: str = Field(..., description="Описание параметра")) -> Dict[str, Any]:
    """Описание инструмента"""
    client = get_client()
    result = client.get("custom-endpoint", params={"param": param})
    return {"success": True, "data": result}
```
