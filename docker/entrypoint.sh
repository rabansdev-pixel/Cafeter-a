#!/bin/sh
set -e

echo "==> Iniciando servicio de Cafetería [Entorno: ${APP_ENV:-development}]..."

# Si se usa base de datos PostgreSQL en producción, espera a que esté lista
if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -q "postgres"; then
    echo "==> Verificando conexión con PostgreSQL..."
    # Lógica de espera si fuera necesario
fi

exec "$@"
