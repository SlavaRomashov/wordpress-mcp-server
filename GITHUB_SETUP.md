# Инструкция по публикации на GitHub

## Шаг 1: Создание репозитория на GitHub

1. Войдите в свой аккаунт GitHub
2. Нажмите кнопку **"+"** в правом верхнем углу → **"New repository"**
3. Заполните форму:
   - **Repository name**: `wordpress-mcp-server` (или другое имя)
   - **Description**: `Полнофункциональный MCP сервер для управления WordPress через ChatGPT`
   - **Visibility**: Выберите Public или Private
   - **НЕ** создавайте README, .gitignore или лицензию (они уже есть)
4. Нажмите **"Create repository"**

## Шаг 2: Подключение локального репозитория к GitHub

После создания репозитория GitHub покажет инструкции. Выполните команды:

```bash
# Добавьте удаленный репозиторий (замените YOUR_USERNAME на ваш username)
git remote add origin https://github.com/YOUR_USERNAME/wordpress-mcp-server.git

# Переименуйте ветку в main (если нужно)
git branch -M main

# Отправьте код на GitHub
git push -u origin main
```

## Альтернативный способ (через SSH)

Если вы используете SSH ключи:

```bash
git remote add origin git@github.com:YOUR_USERNAME/wordpress-mcp-server.git
git branch -M main
git push -u origin main
```

## Шаг 3: Проверка

Откройте ваш репозиторий на GitHub и убедитесь, что все файлы загружены:
- ✅ server.py
- ✅ requirements.txt
- ✅ README.md
- ✅ SETUP.md
- ✅ QUICKSTART.md
- ✅ config.example.env
- ✅ example_usage.py
- ✅ .gitignore
- ✅ PROJECT_STRUCTURE.md

**Важно:** Убедитесь, что файл `.env` НЕ попал в репозиторий (он должен быть в .gitignore)

## Шаг 4: Обновление README (опционально)

После публикации обновите ссылки в README.md:
- Замените `YOUR_USERNAME` на ваш GitHub username
- Добавьте ссылку на репозиторий

## Дальнейшие обновления

Для отправки изменений в будущем:

```bash
git add .
git commit -m "Описание изменений"
git push
```

## Добавление тегов (релизы)

Для создания релиза:

```bash
# Создайте тег
git tag -a v1.0.0 -m "Версия 1.0.0 - Первый релиз"

# Отправьте тег на GitHub
git push origin v1.0.0
```

Затем на GitHub создайте Release через интерфейс: **Releases** → **Create a new release**

## Полезные команды

```bash
# Проверить статус
git status

# Посмотреть историю коммитов
git log

# Посмотреть удаленные репозитории
git remote -v

# Обновить локальный репозиторий
git pull
```

## Безопасность

- ✅ `.env` файл уже в `.gitignore` - не попадет в репозиторий
- ✅ `config.example.env` - безопасный пример конфигурации
- ✅ Никаких паролей или секретов в коде

## Проблемы?

Если возникли проблемы:

1. **Ошибка аутентификации**: Настройте SSH ключи или используйте Personal Access Token
2. **Конфликты**: Используйте `git pull` перед `git push`
3. **Неверный remote**: Проверьте `git remote -v` и при необходимости обновите URL
