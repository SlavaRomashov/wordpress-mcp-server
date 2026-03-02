#!/bin/bash
# Ручная синхронизация - выполните команды на сервере или через SSH

# Вариант 1: Выполнить команды напрямую на сервере
# Подключитесь к серверу: ssh root@85.198.103.185
# Затем выполните команды ниже:

REPO_DIR="/opt/wordpress-mcp-server"
GITHUB_REPO="https://github.com/SlavaRomashov/wordpress-mcp-server.git"

echo "=== Синхронизация WordPress MCP Server ==="
echo ""

# Обновление репозитория
if [ -d "$REPO_DIR" ]; then
    echo "Обновление репозитория..."
    cd "$REPO_DIR"
    git fetch origin
    git reset --hard origin/main
else
    echo "Клонирование репозитория..."
    mkdir -p $(dirname "$REPO_DIR")
    git clone "$GITHUB_REPO" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Установка зависимостей
echo "Установка зависимостей..."
python3 -m pip install --upgrade pip --quiet
python3 -m pip install -r requirements.txt --quiet

# Проверка .env
if [ ! -f .env ]; then
    echo "Создание .env из примера..."
    cp config.example.env .env
    echo "⚠ ВНИМАНИЕ: Настройте файл .env!"
fi

# Обновление systemd service
echo "Обновление systemd service..."
cat > /etc/systemd/system/wordpress-mcp-server.service << 'EOF'
[Unit]
Description=WordPress MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wordpress-mcp-server
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /opt/wordpress-mcp-server/server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# Перезапуск сервиса если запущен
if systemctl is-active --quiet wordpress-mcp-server; then
    echo "Перезапуск сервиса..."
    systemctl restart wordpress-mcp-server
    sleep 2
    systemctl status wordpress-mcp-server --no-pager -l | head -15
fi

echo ""
echo "=== Синхронизация завершена! ==="
echo ""
echo "Проверка статуса:"
git log -1 --oneline
echo ""
systemctl status wordpress-mcp-server --no-pager -l | head -10 || echo "Сервис не запущен"
