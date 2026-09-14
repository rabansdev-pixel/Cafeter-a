#!/usr/bin/env bash
set -e

echo "☕ [DEV] Iniciando Cafetería de Especialidad en modo Desarrollo..."

# Si existe venv local y no se usa docker
if [ -d "venv" ]; then
    echo "Activando venv local..."
    source venv/bin/activate
    export APP_ENV=development
    export FLASK_DEBUG=1
    python run.py
else
    echo "Levantando con Docker Compose (dev)..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
fi
