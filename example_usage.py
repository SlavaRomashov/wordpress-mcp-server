#!/usr/bin/env python3
"""
Пример использования WordPress MCP Server
Этот файл демонстрирует, как можно использовать функции сервера напрямую
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем функции из сервера
from server import (
    get_client,
    wp_create_post,
    wp_list_posts,
    wp_get_post,
    wp_get_site_info
)


def example_usage():
    """Примеры использования функций WordPress MCP Server"""
    
    print("=== WordPress MCP Server - Примеры использования ===\n")
    
    # Проверка подключения
    try:
        print("1. Проверка подключения к WordPress...")
        site_info = wp_get_site_info()
        if site_info.get("success"):
            print(f"✓ Подключено к: {site_info['site']['url']}")
            print(f"  Название сайта: {site_info['site'].get('name', 'N/A')}")
        else:
            print(f"✗ Ошибка: {site_info.get('error', 'Unknown error')}")
            return
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
        print("\nПроверьте настройки в .env файле:")
        print("  - WORDPRESS_URL")
        print("  - WORDPRESS_USERNAME")
        print("  - WORDPRESS_APP_PASSWORD")
        return
    
    print("\n" + "="*50 + "\n")
    
    # Получение списка постов
    try:
        print("2. Получение списка последних постов...")
        posts = wp_list_posts(per_page=5)
        if posts.get("success"):
            print(f"✓ Найдено постов: {posts['count']}")
            for post in posts['posts'][:3]:
                print(f"  - [{post['id']}] {post['title']}")
        else:
            print("✗ Не удалось получить посты")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Создание тестового поста (закомментировано для безопасности)
    """
    try:
        print("3. Создание тестового поста...")
        new_post = wp_create_post(
            title="Тестовый пост через MCP Server",
            content="<p>Это тестовый пост, созданный через WordPress MCP Server.</p>",
            status="draft"  # Используем draft, чтобы не публиковать сразу
        )
        if new_post.get("success"):
            print(f"✓ Пост создан: {new_post['post']['title']}")
            print(f"  ID: {new_post['post']['id']}")
            print(f"  Ссылка: {new_post['post']['link']}")
        else:
            print("✗ Не удалось создать пост")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    """
    
    print("\nПримеры использования завершены!")
    print("\nДля использования через ChatGPT:")
    print("1. Настройте MCP сервер в настройках ChatGPT")
    print("2. Используйте естественный язык для управления WordPress")
    print("3. Например: 'Создай новый пост с заголовком...'")


if __name__ == "__main__":
    example_usage()
