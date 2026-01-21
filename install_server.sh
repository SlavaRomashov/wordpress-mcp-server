#!/bin/bash
# Скрипт установки WordPress MCP Server на сервер

set -e  # Остановка при ошибке

echo "=== Установка WordPress MCP Server ==="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Шаг 1: Обновление системы и установка зависимостей
echo -e "${YELLOW}Шаг 1: Проверка и установка зависимостей...${NC}"
apt-get update -qq
apt-get install -y python3 python3-pip git || yum install -y python3 python3-pip git || dnf install -y python3 python3-pip git

# Шаг 2: Клонирование репозитория
echo -e "${YELLOW}Шаг 2: Клонирование репозитория...${NC}"
REPO_DIR="/opt/wordpress-mcp-server"
if [ -d "$REPO_DIR" ]; then
    echo "Директория $REPO_DIR уже существует. Обновляю..."
    cd "$REPO_DIR"
    git pull
else
    git clone https://github.com/SlavaRomashov/wordpress-mcp-server.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Шаг 3: Установка Python зависимостей
echo -e "${YELLOW}Шаг 3: Установка Python зависимостей...${NC}"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Шаг 4: Создание .env файла если его нет
echo -e "${YELLOW}Шаг 4: Настройка конфигурации...${NC}"
if [ ! -f .env ]; then
    echo "Создаю файл .env..."
    cat > .env << 'EOF'
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=your_application_password
WORDPRESS_TIMEOUT=30
EOF
    echo -e "${YELLOW}ВНИМАНИЕ: Не забудьте отредактировать файл .env с вашими данными WordPress!${NC}"
    echo "Файл находится в: $REPO_DIR/.env"
else
    echo "Файл .env уже существует"
fi

# Шаг 5: Создание systemd service (опционально)
echo -e "${YELLOW}Шаг 5: Создание systemd service...${NC}"
SERVICE_FILE="/etc/systemd/system/wordpress-mcp-server.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=WordPress MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_DIR
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 $REPO_DIR/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "Service файл создан: $SERVICE_FILE"
echo -e "${YELLOW}Для запуска сервиса используйте:${NC}"
echo "  systemctl start wordpress-mcp-server"
echo "  systemctl enable wordpress-mcp-server"
echo "  systemctl status wordpress-mcp-server"

echo ""
echo -e "${GREEN}=== Установка завершена! ===${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте файл .env: nano $REPO_DIR/.env"
echo "2. Запустите сервер:"
echo "   - Вручную: cd $REPO_DIR && python3 server.py"
echo "   - Через systemd: systemctl start wordpress-mcp-server"
echo ""
