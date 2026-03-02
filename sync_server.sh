#!/bin/bash
# Скрипт синхронизации WordPress MCP Server на удаленном сервере через GitHub

set -e

# Конфигурация
SERVER="root@85.198.103.185"
REPO_DIR="/opt/wordpress-mcp-server"
GITHUB_REPO="https://github.com/SlavaRomashov/wordpress-mcp-server.git"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Синхронизация WordPress MCP Server на сервере ===${NC}"
echo -e "${BLUE}Сервер: ${SERVER}${NC}"
echo ""

# Функция для выполнения команд на удаленном сервере
remote_exec() {
    ssh -o StrictHostKeyChecking=no "$SERVER" "$@"
}

# Проверка подключения к серверу
echo -e "${YELLOW}Проверка подключения к серверу...${NC}"
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SERVER" "echo 'Connected'" > /dev/null 2>&1; then
    echo -e "${RED}Ошибка: Не удалось подключиться к серверу ${SERVER}${NC}"
    echo "Убедитесь, что:"
    echo "  1. Сервер доступен"
    echo "  2. SSH ключи настроены (или используйте пароль)"
    echo "  3. Пользователь root имеет доступ"
    exit 1
fi
echo -e "${GREEN}✓ Подключение установлено${NC}"
echo ""

# Шаг 1: Проверка наличия репозитория
echo -e "${YELLOW}Шаг 1: Проверка репозитория...${NC}"
if remote_exec "[ -d $REPO_DIR ]"; then
    echo -e "${GREEN}✓ Репозиторий найден${NC}"
    echo -e "${YELLOW}Обновление из GitHub...${NC}"
    remote_exec "cd $REPO_DIR && git fetch origin && git reset --hard origin/main"
    echo -e "${GREEN}✓ Репозиторий обновлен${NC}"
else
    echo -e "${YELLOW}Репозиторий не найден. Клонирование...${NC}"
    remote_exec "mkdir -p $(dirname $REPO_DIR) && git clone $GITHUB_REPO $REPO_DIR"
    echo -e "${GREEN}✓ Репозиторий клонирован${NC}"
fi
echo ""

# Шаг 2: Установка/обновление зависимостей
echo -e "${YELLOW}Шаг 2: Проверка Python зависимостей...${NC}"
remote_exec "cd $REPO_DIR && python3 -m pip install --upgrade pip --quiet && python3 -m pip install -r requirements.txt --quiet"
echo -e "${GREEN}✓ Зависимости установлены/обновлены${NC}"
echo ""

# Шаг 3: Проверка .env файла
echo -e "${YELLOW}Шаг 3: Проверка конфигурации...${NC}"
if remote_exec "[ ! -f $REPO_DIR/.env ]"; then
    echo -e "${YELLOW}⚠ Файл .env не найден. Создаю из примера...${NC}"
    remote_exec "cd $REPO_DIR && cp config.example.env .env"
    echo -e "${RED}⚠ ВНИМАНИЕ: Не забудьте настроить файл .env на сервере!${NC}"
    echo "   Выполните: ssh $SERVER 'nano $REPO_DIR/.env'"
else
    echo -e "${GREEN}✓ Файл .env существует${NC}"
    echo -e "${YELLOW}⚠ Файл .env не будет перезаписан (защита ваших настроек)${NC}"
fi
echo ""

# Шаг 4: Обновление systemd service
echo -e "${YELLOW}Шаг 4: Обновление systemd service...${NC}"
remote_exec "cat > /etc/systemd/system/wordpress-mcp-server.service << 'EOFSERVICE'
[Unit]
Description=WordPress MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_DIR
Environment=\"PATH=/usr/bin:/usr/local/bin\"
ExecStart=/usr/bin/python3 $REPO_DIR/server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOFSERVICE
"
remote_exec "systemctl daemon-reload"
echo -e "${GREEN}✓ Systemd service обновлен${NC}"
echo ""

# Шаг 5: Проверка статуса сервиса
echo -e "${YELLOW}Шаг 5: Проверка статуса сервиса...${NC}"
if remote_exec "systemctl is-active --quiet wordpress-mcp-server" 2>/dev/null; then
    echo -e "${GREEN}✓ Сервис запущен. Перезапускаю...${NC}"
    remote_exec "systemctl restart wordpress-mcp-server"
    sleep 2
    if remote_exec "systemctl is-active --quiet wordpress-mcp-server" 2>/dev/null; then
        echo -e "${GREEN}✓ Сервис успешно перезапущен${NC}"
    else
        echo -e "${RED}⚠ Ошибка при перезапуске сервиса${NC}"
        remote_exec "systemctl status wordpress-mcp-server --no-pager -l" || true
    fi
else
    echo -e "${YELLOW}⚠ Сервис не запущен${NC}"
    echo -e "${YELLOW}Для запуска выполните:${NC}"
    echo "  ssh $SERVER 'systemctl start wordpress-mcp-server'"
    echo "  ssh $SERVER 'systemctl enable wordpress-mcp-server'"
fi
echo ""

# Шаг 6: Показ статуса
echo -e "${YELLOW}Текущий статус:${NC}"
remote_exec "cd $REPO_DIR && echo 'Версия репозитория:' && git log -1 --oneline && echo '' && echo 'Статус сервиса:' && systemctl status wordpress-mcp-server --no-pager -l | head -10 || true"
echo ""

echo -e "${GREEN}=== Синхронизация завершена! ===${NC}"
echo ""
echo -e "${BLUE}Полезные команды:${NC}"
echo "  Просмотр логов:     ssh $SERVER 'journalctl -u wordpress-mcp-server -f'"
echo "  Статус сервиса:     ssh $SERVER 'systemctl status wordpress-mcp-server'"
echo "  Перезапуск:         ssh $SERVER 'systemctl restart wordpress-mcp-server'"
echo "  Редактирование .env: ssh $SERVER 'nano $REPO_DIR/.env'"
echo ""
