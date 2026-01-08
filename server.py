#!/usr/bin/env python3
"""
WordPress MCP Server
Полнофункциональный MCP сервер для управления WordPress через ChatGPT
"""

import os
import base64
import mimetypes
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Загружаем переменные окружения
load_dotenv()

# Инициализация MCP сервера
mcp = FastMCP("WordPress MCP Server")

# Конфигурация WordPress
WORDPRESS_URL = os.getenv("WORDPRESS_URL", "").rstrip("/")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME", "")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD", "")
WORDPRESS_TIMEOUT = int(os.getenv("WORDPRESS_TIMEOUT", "30"))

# Базовый URL для REST API
API_BASE = f"{WORDPRESS_URL}/wp-json/wp/v2"


class WordPressClient:
    """Клиент для работы с WordPress REST API"""
    
    def __init__(self):
        if not all([WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD]):
            raise ValueError("Необходимо настроить WORDPRESS_URL, WORDPRESS_USERNAME и WORDPRESS_APP_PASSWORD")
        
        # Создаем Basic Auth заголовок
        credentials = f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
        
        self.client = httpx.Client(
            timeout=WORDPRESS_TIMEOUT,
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполняет HTTP запрос к WordPress API"""
        url = urljoin(API_BASE + "/", endpoint.lstrip("/"))
        
        try:
            response = self.client.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Для DELETE запросов может не быть тела ответа
            if response.status_code == 204 or not response.text:
                return {"deleted": True, "status": response.status_code}
            
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            if e.response.status_code == 401:
                error_msg += ": Ошибка аутентификации. Проверьте WORDPRESS_USERNAME и WORDPRESS_APP_PASSWORD"
            elif e.response.status_code == 403:
                error_msg += ": Доступ запрещен. Проверьте права пользователя"
            elif e.response.status_code == 404:
                error_msg += ": Ресурс не найден"
            elif e.response.status_code == 500:
                error_msg += ": Внутренняя ошибка сервера WordPress"
            
            if e.response.text:
                try:
                    error_data = e.response.json()
                    if isinstance(error_data, dict):
                        error_msg += f" - {error_data.get('message', error_data.get('code', e.response.text))}"
                    else:
                        error_msg += f" - {str(error_data)}"
                except:
                    # Если не JSON, берем первые 200 символов текста
                    text = e.response.text[:200] if len(e.response.text) > 200 else e.response.text
                    error_msg += f" - {text}"
            raise Exception(error_msg)
        except httpx.TimeoutException:
            raise Exception(f"Таймаут запроса к WordPress (превышено {WORDPRESS_TIMEOUT} секунд)")
        except httpx.ConnectError:
            raise Exception(f"Не удалось подключиться к {WORDPRESS_URL}. Проверьте URL и доступность сайта")
        except httpx.RequestError as e:
            raise Exception(f"Ошибка подключения: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET запрос"""
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """POST запрос"""
        return self._request("POST", endpoint, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """PUT запрос"""
        return self._request("PUT", endpoint, json=data)
    
    def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """DELETE запрос"""
        return self._request("DELETE", endpoint, params=params)
    
    def upload_media(self, file_url: Optional[str] = None, file_path: Optional[str] = None, 
                     title: Optional[str] = None, alt_text: Optional[str] = None) -> Dict[str, Any]:
        """Загружает медиафайл по URL или из локального файла"""
        file_content = None
        file_name = None
        
        # Загружаем файл из URL или локального файла
        if file_url:
            try:
                file_response = httpx.get(file_url, timeout=WORDPRESS_TIMEOUT)
                file_response.raise_for_status()
                file_content = file_response.content
                file_name = os.path.basename(file_url)
            except Exception as e:
                raise Exception(f"Не удалось загрузить файл по URL: {str(e)}")
        elif file_path:
            try:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Файл не найден: {file_path}")
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                file_name = os.path.basename(file_path)
            except Exception as e:
                raise Exception(f"Не удалось прочитать локальный файл: {str(e)}")
        else:
            raise ValueError("Необходимо указать file_url или file_path")
        
        if not file_content or not file_name:
            raise ValueError("Не удалось получить содержимое файла")
        
        # Определяем MIME тип
        mime_type, _ = mimetypes.guess_type(file_name)
        content_type = mime_type or 'application/octet-stream'
        
        # Загружаем в WordPress
        files = {
            "file": (file_name, file_content, content_type)
        }
        data = {}
        if title:
            data["title"] = title
        if alt_text:
            data["alt_text"] = alt_text
        
        url = urljoin(API_BASE + "/", "media")
        # Для загрузки файлов нужно использовать multipart/form-data
        headers = {
            "Authorization": self.auth_header,
            "Accept": "application/json"
        }
        # Убираем Content-Type из заголовков, httpx установит его автоматически с boundary
        
        try:
            response = self.client.post(url, files=files, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: Не удалось загрузить медиафайл"
            if e.response.text:
                try:
                    error_data = e.response.json()
                    if isinstance(error_data, dict):
                        error_msg += f" - {error_data.get('message', error_data.get('code', e.response.text))}"
                except:
                    pass
            raise Exception(error_msg)
        except httpx.RequestError as e:
            raise Exception(f"Ошибка при загрузке медиафайла: {str(e)}")
    
    def close(self):
        """Закрывает HTTP клиент"""
        self.client.close()


# Глобальный клиент WordPress
wp_client: Optional[WordPressClient] = None


def get_client() -> WordPressClient:
    """Получает или создает клиент WordPress"""
    global wp_client
    if wp_client is None:
        try:
            wp_client = WordPressClient()
        except ValueError as e:
            raise Exception(f"Ошибка конфигурации: {str(e)}. Проверьте настройки в .env файле.")
    return wp_client


# ==================== ИНСТРУМЕНТЫ ДЛЯ ПОСТОВ ====================

@mcp.tool()
def wp_create_post(
    title: str = Field(..., description="Заголовок поста"),
    content: str = Field(..., description="Содержимое поста (HTML или текст)"),
    status: str = Field("publish", description="Статус поста: draft, publish, pending, private"),
    excerpt: Optional[str] = Field(None, description="Краткое описание поста"),
    categories: Optional[List[int]] = Field(None, description="ID категорий"),
    tags: Optional[List[int]] = Field(None, description="ID тегов"),
    featured_media: Optional[int] = Field(None, description="ID изображения для обложки")
) -> Dict[str, Any]:
    """Создает новый пост в WordPress"""
    client = get_client()
    data = {
        "title": title,
        "content": content,
        "status": status
    }
    if excerpt:
        data["excerpt"] = excerpt
    if categories:
        data["categories"] = categories
    if tags:
        data["tags"] = tags
    if featured_media:
        data["featured_media"] = featured_media
    
    result = client.post("posts", data=data)
    return {
        "success": True,
        "message": f"Пост '{title}' успешно создан",
        "post": {
            "id": result["id"],
            "title": result["title"]["rendered"],
            "link": result["link"],
            "status": result["status"]
        }
    }


@mcp.tool()
def wp_get_post(post_id: int = Field(..., description="ID поста")) -> Dict[str, Any]:
    """Получает пост по ID"""
    client = get_client()
    result = client.get(f"posts/{post_id}")
    return {
        "success": True,
        "post": {
            "id": result["id"],
            "title": result["title"]["rendered"],
            "content": result["content"]["rendered"],
            "excerpt": result["excerpt"]["rendered"],
            "status": result["status"],
            "date": result["date"],
            "link": result["link"],
            "author": result["author"],
            "categories": result["categories"],
            "tags": result["tags"]
        }
    }


@mcp.tool()
def wp_list_posts(
    per_page: int = Field(10, description="Количество постов на странице"),
    page: int = Field(1, description="Номер страницы"),
    status: Optional[str] = Field(None, description="Фильтр по статусу: publish, draft, pending, private"),
    search: Optional[str] = Field(None, description="Поисковый запрос"),
    categories: Optional[List[int]] = Field(None, description="Фильтр по категориям (ID)")
) -> Dict[str, Any]:
    """Получает список постов"""
    client = get_client()
    params = {
        "per_page": per_page,
        "page": page
    }
    if status:
        params["status"] = status
    if search:
        params["search"] = search
    if categories:
        params["categories"] = ",".join(map(str, categories))
    
    result = client.get("posts", params=params)
    posts = []
    for post in result:
        posts.append({
            "id": post["id"],
            "title": post["title"]["rendered"],
            "excerpt": post["excerpt"]["rendered"],
            "status": post["status"],
            "date": post["date"],
            "link": post["link"]
        })
    
    return {
        "success": True,
        "count": len(posts),
        "posts": posts
    }


@mcp.tool()
def wp_update_post(
    post_id: int = Field(..., description="ID поста для обновления"),
    title: Optional[str] = Field(None, description="Новый заголовок"),
    content: Optional[str] = Field(None, description="Новое содержимое"),
    status: Optional[str] = Field(None, description="Новый статус"),
    excerpt: Optional[str] = Field(None, description="Новое краткое описание"),
    categories: Optional[List[int]] = Field(None, description="ID категорий"),
    tags: Optional[List[int]] = Field(None, description="ID тегов")
) -> Dict[str, Any]:
    """Обновляет существующий пост"""
    client = get_client()
    data = {}
    if title:
        data["title"] = title
    if content:
        data["content"] = content
    if status:
        data["status"] = status
    if excerpt:
        data["excerpt"] = excerpt
    if categories:
        data["categories"] = categories
    if tags:
        data["tags"] = tags
    
    result = client.put(f"posts/{post_id}", data=data)
    return {
        "success": True,
        "message": f"Пост #{post_id} успешно обновлен",
        "post": {
            "id": result["id"],
            "title": result["title"]["rendered"],
            "link": result["link"],
            "status": result["status"]
        }
    }


@mcp.tool()
def wp_delete_post(
    post_id: int = Field(..., description="ID поста для удаления"),
    force: bool = Field(False, description="Принудительное удаление (минуя корзину)")
) -> Dict[str, Any]:
    """Удаляет пост"""
    client = get_client()
    params = {"force": force} if force else {}
    result = client.delete(f"posts/{post_id}", params=params)
    return {
        "success": True,
        "message": f"Пост #{post_id} успешно удален",
        "deleted": result.get("deleted", False)
    }


# ==================== ИНСТРУМЕНТЫ ДЛЯ СТРАНИЦ ====================

@mcp.tool()
def wp_create_page(
    title: str = Field(..., description="Заголовок страницы"),
    content: str = Field(..., description="Содержимое страницы (HTML или текст)"),
    status: str = Field("publish", description="Статус страницы: draft, publish, pending, private"),
    excerpt: Optional[str] = Field(None, description="Краткое описание страницы"),
    parent: Optional[int] = Field(None, description="ID родительской страницы"),
    template: Optional[str] = Field(None, description="Шаблон страницы")
) -> Dict[str, Any]:
    """Создает новую страницу в WordPress"""
    client = get_client()
    data = {
        "title": title,
        "content": content,
        "status": status
    }
    if excerpt:
        data["excerpt"] = excerpt
    if parent:
        data["parent"] = parent
    if template:
        data["template"] = template
    
    result = client.post("pages", data=data)
    return {
        "success": True,
        "message": f"Страница '{title}' успешно создана",
        "page": {
            "id": result["id"],
            "title": result["title"]["rendered"],
            "link": result["link"],
            "status": result["status"]
        }
    }


@mcp.tool()
def wp_get_page(page_id: int = Field(..., description="ID страницы")) -> Dict[str, Any]:
    """Получает страницу по ID"""
    client = get_client()
    result = client.get(f"pages/{page_id}")
    return {
        "success": True,
        "page": {
            "id": result["id"],
            "title": result["title"]["rendered"],
            "content": result["content"]["rendered"],
            "excerpt": result["excerpt"]["rendered"],
            "status": result["status"],
            "date": result["date"],
            "link": result["link"],
            "parent": result.get("parent", 0)
        }
    }


@mcp.tool()
def wp_list_pages(
    per_page: int = Field(10, description="Количество страниц на странице"),
    page: int = Field(1, description="Номер страницы"),
    status: Optional[str] = Field(None, description="Фильтр по статусу"),
    search: Optional[str] = Field(None, description="Поисковый запрос"),
    parent: Optional[int] = Field(None, description="ID родительской страницы")
) -> Dict[str, Any]:
    """Получает список страниц"""
    client = get_client()
    params = {
        "per_page": per_page,
        "page": page
    }
    if status:
        params["status"] = status
    if search:
        params["search"] = search
    if parent:
        params["parent"] = parent
    
    result = client.get("pages", params=params)
    pages = []
    for page_item in result:
        pages.append({
            "id": page_item["id"],
            "title": page_item["title"]["rendered"],
            "excerpt": page_item["excerpt"]["rendered"],
            "status": page_item["status"],
            "date": page_item["date"],
            "link": page_item["link"],
            "parent": page_item.get("parent", 0)
        })
    
    return {
        "success": True,
        "count": len(pages),
        "pages": pages
    }


@mcp.tool()
def wp_update_page(
    page_id: int = Field(..., description="ID страницы для обновления"),
    title: Optional[str] = Field(None, description="Новый заголовок"),
    content: Optional[str] = Field(None, description="Новое содержимое"),
    status: Optional[str] = Field(None, description="Новый статус"),
    excerpt: Optional[str] = Field(None, description="Новое краткое описание"),
    parent: Optional[int] = Field(None, description="ID родительской страницы")
) -> Dict[str, Any]:
    """Обновляет существующую страницу"""
    client = get_client()
    data = {}
    if title:
        data["title"] = title
    if content:
        data["content"] = content
    if status:
        data["status"] = status
    if excerpt:
        data["excerpt"] = excerpt
    if parent:
        data["parent"] = parent
    
    result = client.put(f"pages/{page_id}", data=data)
    return {
        "success": True,
        "message": f"Страница #{page_id} успешно обновлена",
        "page": {
            "id": result["id"],
            "title": result["title"]["rendered"],
            "link": result["link"],
            "status": result["status"]
        }
    }


@mcp.tool()
def wp_delete_page(
    page_id: int = Field(..., description="ID страницы для удаления"),
    force: bool = Field(False, description="Принудительное удаление")
) -> Dict[str, Any]:
    """Удаляет страницу"""
    client = get_client()
    params = {"force": force} if force else {}
    result = client.delete(f"pages/{page_id}", params=params)
    return {
        "success": True,
        "message": f"Страница #{page_id} успешно удалена",
        "deleted": result.get("deleted", False)
    }


# ==================== ИНСТРУМЕНТЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ====================

@mcp.tool()
def wp_get_user(user_id: int = Field(..., description="ID пользователя")) -> Dict[str, Any]:
    """Получает пользователя по ID"""
    client = get_client()
    result = client.get(f"users/{user_id}")
    return {
        "success": True,
        "user": {
            "id": result["id"],
            "name": result["name"],
            "username": result["username"],
            "email": result["email"],
            "url": result.get("url", ""),
            "description": result.get("description", ""),
            "link": result["link"],
            "roles": result.get("roles", [])
        }
    }


@mcp.tool()
def wp_list_users(
    per_page: int = Field(10, description="Количество пользователей на странице"),
    page: int = Field(1, description="Номер страницы"),
    search: Optional[str] = Field(None, description="Поисковый запрос"),
    roles: Optional[List[str]] = Field(None, description="Фильтр по ролям")
) -> Dict[str, Any]:
    """Получает список пользователей"""
    client = get_client()
    params = {
        "per_page": per_page,
        "page": page
    }
    if search:
        params["search"] = search
    if roles:
        params["roles"] = ",".join(roles)
    
    result = client.get("users", params=params)
    users = []
    for user in result:
        users.append({
            "id": user["id"],
            "name": user["name"],
            "username": user["username"],
            "email": user["email"],
            "link": user["link"],
            "roles": user.get("roles", [])
        })
    
    return {
        "success": True,
        "count": len(users),
        "users": users
    }


@mcp.tool()
def wp_create_user(
    username: str = Field(..., description="Имя пользователя"),
    email: str = Field(..., description="Email пользователя"),
    password: str = Field(..., description="Пароль пользователя"),
    name: Optional[str] = Field(None, description="Отображаемое имя"),
    roles: Optional[List[str]] = Field(None, description="Роли пользователя")
) -> Dict[str, Any]:
    """Создает нового пользователя"""
    client = get_client()
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    if name:
        data["name"] = name
    if roles:
        data["roles"] = roles
    
    result = client.post("users", data=data)
    return {
        "success": True,
        "message": f"Пользователь '{username}' успешно создан",
        "user": {
            "id": result["id"],
            "username": result["username"],
            "email": result["email"],
            "name": result["name"]
        }
    }


@mcp.tool()
def wp_update_user(
    user_id: int = Field(..., description="ID пользователя для обновления"),
    email: Optional[str] = Field(None, description="Новый email"),
    name: Optional[str] = Field(None, description="Новое отображаемое имя"),
    password: Optional[str] = Field(None, description="Новый пароль"),
    roles: Optional[List[str]] = Field(None, description="Новые роли")
) -> Dict[str, Any]:
    """Обновляет пользователя"""
    client = get_client()
    data = {}
    if email:
        data["email"] = email
    if name:
        data["name"] = name
    if password:
        data["password"] = password
    if roles:
        data["roles"] = roles
    
    result = client.put(f"users/{user_id}", data=data)
    return {
        "success": True,
        "message": f"Пользователь #{user_id} успешно обновлен",
        "user": {
            "id": result["id"],
            "username": result["username"],
            "email": result["email"],
            "name": result["name"]
        }
    }


# ==================== ИНСТРУМЕНТЫ ДЛЯ МЕДИА ====================

@mcp.tool()
def wp_upload_media(
    file_url: Optional[str] = Field(None, description="URL файла для загрузки"),
    file_path: Optional[str] = Field(None, description="Путь к локальному файлу"),
    title: Optional[str] = Field(None, description="Заголовок медиафайла"),
    alt_text: Optional[str] = Field(None, description="Альтернативный текст для изображения")
) -> Dict[str, Any]:
    """Загружает медиафайл в WordPress из URL или локального файла"""
    if not file_url and not file_path:
        return {
            "success": False,
            "error": "Необходимо указать file_url или file_path"
        }
    
    client = get_client()
    result = client.upload_media(file_url=file_url, file_path=file_path, title=title, alt_text=alt_text)
    return {
        "success": True,
        "message": "Медиафайл успешно загружен",
        "media": {
            "id": result["id"],
            "title": result["title"]["rendered"],
            "source_url": result["source_url"],
            "link": result["link"],
            "media_type": result.get("media_type", ""),
            "mime_type": result.get("mime_type", "")
        }
    }


@mcp.tool()
def wp_get_media(media_id: int = Field(..., description="ID медиафайла")) -> Dict[str, Any]:
    """Получает медиафайл по ID"""
    client = get_client()
    result = client.get(f"media/{media_id}")
    return {
        "success": True,
        "media": {
            "id": result["id"],
            "title": result["title"]["rendered"],
            "source_url": result["source_url"],
            "link": result["link"],
            "media_type": result.get("media_type", ""),
            "mime_type": result.get("mime_type", ""),
            "alt_text": result.get("alt_text", "")
        }
    }


@mcp.tool()
def wp_list_media(
    per_page: int = Field(10, description="Количество медиафайлов на странице"),
    page: int = Field(1, description="Номер страницы"),
    media_type: Optional[str] = Field(None, description="Тип медиа: image, video, audio, application")
) -> Dict[str, Any]:
    """Получает список медиафайлов"""
    client = get_client()
    params = {
        "per_page": per_page,
        "page": page
    }
    if media_type:
        params["media_type"] = media_type
    
    result = client.get("media", params=params)
    media_list = []
    for media in result:
        media_list.append({
            "id": media["id"],
            "title": media["title"]["rendered"],
            "source_url": media["source_url"],
            "link": media["link"],
            "media_type": media.get("media_type", ""),
            "mime_type": media.get("mime_type", "")
        })
    
    return {
        "success": True,
        "count": len(media_list),
        "media": media_list
    }


# ==================== ИНСТРУМЕНТЫ ДЛЯ КОММЕНТАРИЕВ ====================

@mcp.tool()
def wp_get_comment(comment_id: int = Field(..., description="ID комментария")) -> Dict[str, Any]:
    """Получает комментарий по ID"""
    client = get_client()
    result = client.get(f"comments/{comment_id}")
    return {
        "success": True,
        "comment": {
            "id": result["id"],
            "post": result["post"],
            "author_name": result["author_name"],
            "author_email": result.get("author_email", ""),
            "content": result["content"]["rendered"],
            "date": result["date"],
            "status": result["status"],
            "link": result["link"]
        }
    }


@mcp.tool()
def wp_list_comments(
    per_page: int = Field(10, description="Количество комментариев на странице"),
    page: int = Field(1, description="Номер страницы"),
    post: Optional[int] = Field(None, description="ID поста для фильтрации"),
    status: Optional[str] = Field(None, description="Статус комментария: approved, hold, spam, trash")
) -> Dict[str, Any]:
    """Получает список комментариев"""
    client = get_client()
    params = {
        "per_page": per_page,
        "page": page
    }
    if post:
        params["post"] = post
    if status:
        params["status"] = status
    
    result = client.get("comments", params=params)
    comments = []
    for comment in result:
        comments.append({
            "id": comment["id"],
            "post": comment["post"],
            "author_name": comment["author_name"],
            "content": comment["content"]["rendered"],
            "date": comment["date"],
            "status": comment["status"],
            "link": comment["link"]
        })
    
    return {
        "success": True,
        "count": len(comments),
        "comments": comments
    }


@mcp.tool()
def wp_create_comment(
    post: int = Field(..., description="ID поста"),
    content: str = Field(..., description="Содержимое комментария"),
    author_name: str = Field(..., description="Имя автора"),
    author_email: Optional[str] = Field(None, description="Email автора"),
    parent: Optional[int] = Field(None, description="ID родительского комментария")
) -> Dict[str, Any]:
    """Создает новый комментарий"""
    client = get_client()
    data = {
        "post": post,
        "content": content,
        "author_name": author_name
    }
    if author_email:
        data["author_email"] = author_email
    if parent:
        data["parent"] = parent
    
    result = client.post("comments", data=data)
    return {
        "success": True,
        "message": "Комментарий успешно создан",
        "comment": {
            "id": result["id"],
            "post": result["post"],
            "author_name": result["author_name"],
            "content": result["content"]["rendered"],
            "status": result["status"]
        }
    }


@mcp.tool()
def wp_update_comment(
    comment_id: int = Field(..., description="ID комментария для обновления"),
    content: Optional[str] = Field(None, description="Новое содержимое"),
    status: Optional[str] = Field(None, description="Новый статус")
) -> Dict[str, Any]:
    """Обновляет комментарий"""
    client = get_client()
    data = {}
    if content:
        data["content"] = content
    if status:
        data["status"] = status
    
    result = client.put(f"comments/{comment_id}", data=data)
    return {
        "success": True,
        "message": f"Комментарий #{comment_id} успешно обновлен",
        "comment": {
            "id": result["id"],
            "status": result["status"]
        }
    }


@mcp.tool()
def wp_delete_comment(
    comment_id: int = Field(..., description="ID комментария для удаления"),
    force: bool = Field(False, description="Принудительное удаление")
) -> Dict[str, Any]:
    """Удаляет комментарий"""
    client = get_client()
    params = {"force": force} if force else {}
    result = client.delete(f"comments/{comment_id}", params=params)
    return {
        "success": True,
        "message": f"Комментарий #{comment_id} успешно удален",
        "deleted": result.get("deleted", False)
    }


# ==================== ИНСТРУМЕНТЫ ДЛЯ КАТЕГОРИЙ ====================

@mcp.tool()
def wp_list_categories(
    per_page: int = Field(100, description="Количество категорий"),
    page: int = Field(1, description="Номер страницы"),
    search: Optional[str] = Field(None, description="Поисковый запрос"),
    parent: Optional[int] = Field(None, description="ID родительской категории")
) -> Dict[str, Any]:
    """Получает список категорий"""
    client = get_client()
    params = {
        "per_page": per_page,
        "page": page
    }
    if search:
        params["search"] = search
    if parent is not None:
        params["parent"] = parent
    
    result = client.get("categories", params=params)
    categories = []
    for category in result:
        categories.append({
            "id": category["id"],
            "name": category["name"],
            "slug": category["slug"],
            "description": category.get("description", ""),
            "count": category.get("count", 0),
            "parent": category.get("parent", 0)
        })
    
    return {
        "success": True,
        "count": len(categories),
        "categories": categories
    }


@mcp.tool()
def wp_get_category(category_id: int = Field(..., description="ID категории")) -> Dict[str, Any]:
    """Получает категорию по ID"""
    client = get_client()
    result = client.get(f"categories/{category_id}")
    return {
        "success": True,
        "category": {
            "id": result["id"],
            "name": result["name"],
            "slug": result["slug"],
            "description": result.get("description", ""),
            "count": result.get("count", 0),
            "parent": result.get("parent", 0)
        }
    }


@mcp.tool()
def wp_create_category(
    name: str = Field(..., description="Название категории"),
    description: Optional[str] = Field(None, description="Описание категории"),
    slug: Optional[str] = Field(None, description="URL-слаг категории"),
    parent: Optional[int] = Field(None, description="ID родительской категории")
) -> Dict[str, Any]:
    """Создает новую категорию"""
    client = get_client()
    data = {"name": name}
    if description:
        data["description"] = description
    if slug:
        data["slug"] = slug
    if parent:
        data["parent"] = parent
    
    result = client.post("categories", data=data)
    return {
        "success": True,
        "message": f"Категория '{name}' успешно создана",
        "category": {
            "id": result["id"],
            "name": result["name"],
            "slug": result["slug"]
        }
    }


# ==================== ИНСТРУМЕНТЫ ДЛЯ ТЕГОВ ====================

@mcp.tool()
def wp_list_tags(
    per_page: int = Field(100, description="Количество тегов"),
    page: int = Field(1, description="Номер страницы"),
    search: Optional[str] = Field(None, description="Поисковый запрос")
) -> Dict[str, Any]:
    """Получает список тегов"""
    client = get_client()
    params = {
        "per_page": per_page,
        "page": page
    }
    if search:
        params["search"] = search
    
    result = client.get("tags", params=params)
    tags = []
    for tag in result:
        tags.append({
            "id": tag["id"],
            "name": tag["name"],
            "slug": tag["slug"],
            "description": tag.get("description", ""),
            "count": tag.get("count", 0)
        })
    
    return {
        "success": True,
        "count": len(tags),
        "tags": tags
    }


@mcp.tool()
def wp_get_tag(tag_id: int = Field(..., description="ID тега")) -> Dict[str, Any]:
    """Получает тег по ID"""
    client = get_client()
    result = client.get(f"tags/{tag_id}")
    return {
        "success": True,
        "tag": {
            "id": result["id"],
            "name": result["name"],
            "slug": result["slug"],
            "description": result.get("description", ""),
            "count": result.get("count", 0)
        }
    }


@mcp.tool()
def wp_create_tag(
    name: str = Field(..., description="Название тега"),
    description: Optional[str] = Field(None, description="Описание тега"),
    slug: Optional[str] = Field(None, description="URL-слаг тега")
) -> Dict[str, Any]:
    """Создает новый тег"""
    client = get_client()
    data = {"name": name}
    if description:
        data["description"] = description
    if slug:
        data["slug"] = slug
    
    result = client.post("tags", data=data)
    return {
        "success": True,
        "message": f"Тег '{name}' успешно создан",
        "tag": {
            "id": result["id"],
            "name": result["name"],
            "slug": result["slug"]
        }
    }


# ==================== ИНСТРУМЕНТЫ ДЛЯ ИНФОРМАЦИИ О САЙТЕ ====================

@mcp.tool()
def wp_get_site_info() -> Dict[str, Any]:
    """Получает информацию о WordPress сайте"""
    client = get_client()
    # Получаем информацию через различные endpoints
    try:
        # Получаем информацию о сайте через корневой REST API endpoint
        site_url = f"{WORDPRESS_URL}/wp-json"
        try:
            response = client.client.get(site_url, timeout=WORDPRESS_TIMEOUT)
            response.raise_for_status()
            site_info = response.json()
        except:
            site_info = {}
        
        # Получаем информацию о текущем пользователе
        try:
            user_info = client.get("users/me")
        except:
            user_info = None
        
        return {
            "success": True,
            "site": {
                "url": WORDPRESS_URL,
                "name": site_info.get("name", ""),
                "description": site_info.get("description", ""),
                "home": site_info.get("home", WORDPRESS_URL),
                "namespaces": site_info.get("namespaces", []),
                "authentication": {
                    "enabled": True,
                    "username": WORDPRESS_USERNAME
                },
                "current_user": {
                    "id": user_info["id"] if user_info else None,
                    "name": user_info["name"] if user_info else None,
                    "username": user_info["username"] if user_info else None,
                    "roles": user_info.get("roles", []) if user_info else []
                } if user_info else None
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "site": {
                "url": WORDPRESS_URL,
                "authentication": {
                    "enabled": True,
                    "username": WORDPRESS_USERNAME
                }
            }
        }


# Запуск сервера
if __name__ == "__main__":
    mcp.run()
