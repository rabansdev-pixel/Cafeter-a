#!/usr/bin/env bash
set -e

echo "🛡️ [SNYK] Escaneando vulnerabilidades de seguridad..."

if ! command -v snyk &> /dev/null; then
    echo "⚠️ Snyk CLI no está instalado en el PATH. Puedes instalarlo con: npm install -g snyk"
    echo "O ejecutarlo mediante npx con: npx snyk test"
fi

echo "1. Escaneando dependencias (requirements.txt)..."
if command -v snyk &> /dev/null; then
    snyk test --file=requirements.txt || true
    echo "2. Escaneando código fuente (SAST)..."
    snyk code test app/ || true
    echo "3. Escaneando Dockerfile..."
    snyk container test docker/Dockerfile || true
else
    echo "Ejecutando con npx..."
    npx -y snyk test --file=requirements.txt || true
fi
