#!/bin/bash
# Скрипт для запуска WordPress MCP Server через Cloudflare Tunnel
# Использование: ./start_with_tunnel.sh

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== WordPress MCP Server с Cloudflare Tunnel ===${NC}\n"

# Проверка наличия cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}Ошибка: cloudflared не установлен${NC}"
    echo "Установите cloudflared:"
    echo "  macOS: brew install cloudflare/cloudflare/cloudflared"
    echo "  Linux: sudo snap install cloudflared"
    echo "  Или скачайте с https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
    exit 1
fi

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Ошибка: Python 3 не установлен${NC}"
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo -e "${YELLOW}Предупреждение: файл .env не найден${NC}"
    echo "Создайте файл .env на основе config.example.env"
    exit 1
fi

# Проверка конфигурации туннеля
if [ ! -f cloudflare-tunnel-config.yaml ]; then
    echo -e "${YELLOW}Предупреждение: cloudflare-tunnel-config.yaml не найден${NC}"
    echo "Создайте конфигурационный файл для Cloudflare Tunnel"
    echo "См. инструкции в CLOUDFLARE_TUNNEL_SETUP.md"
    exit 1
fi

# Загрузка переменных окружения
export $(cat .env | grep -v '^#' | xargs)

# Проверка обязательных переменных
if [ -z "$WORDPRESS_URL" ] || [ -z "$WORDPRESS_USERNAME" ] || [ -z "$WORDPRESS_APP_PASSWORD" ]; then
    echo -e "${RED}Ошибка: не все обязательные переменные окружения установлены${NC}"
    echo "Проверьте файл .env"
    exit 1
fi

echo -e "${GREEN}✓ Конфигурация проверена${NC}\n"

# Определяем режим запуска
TUNNEL_MODE=${1:-stdio}

if [ "$TUNNEL_MODE" = "http" ]; then
    echo -e "${YELLOW}Режим HTTP через Cloudflare Tunnel${NC}"
    echo "Запуск MCP сервера в HTTP режиме..."
    echo "Примечание: Стандартный MCP работает через stdio, HTTP режим требует дополнительной настройки"
    
    # Запуск туннеля в фоне
    echo "Запуск Cloudflare Tunnel..."
    cloudflared tunnel --config cloudflare-tunnel-config.yaml run &
    TUNNEL_PID=$!
    
    # Ожидание запуска туннеля
    sleep 3
    
    echo -e "${GREEN}Туннель запущен (PID: $TUNNEL_PID)${NC}"
    echo "MCP сервер доступен через туннель"
    
    # Ожидание завершения
    wait $TUNNEL_PID
else
    echo -e "${GREEN}Режим stdio (стандартный MCP)${NC}"
    echo "Запуск WordPress MCP Server..."
    echo ""
    echo -e "${YELLOW}Примечание:${NC}"
    echo "Для работы через Cloudflare Tunnel с ChatGPT, настройте туннель отдельно"
    echo "и используйте стандартную конфигурацию MCP в ChatGPT"
    echo ""
    
    # Запуск MCP сервера
    python3 server.py
fi
