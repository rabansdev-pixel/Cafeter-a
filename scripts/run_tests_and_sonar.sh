#!/usr/bin/env bash
set -e

echo "🧪 [TEST & SONAR] Ejecutando suite de pruebas unitarias y cobertura..."

# Ejecutar pytest y generar coverage.xml para SonarQube
pytest tests/ --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml

echo "✅ Pruebas completadas y archivo coverage.xml generado."

# Si sonar-scanner está instalado en el sistema o en contenedor
if command -v sonar-scanner &> /dev/null; then
    echo "🔍 Iniciando análisis estático con SonarScanner..."
    sonar-scanner
else
    echo "💡 Nota: sonar-scanner no está instalado localmente en el PATH."
    echo "   Puedes ejecutar SonarQube con: docker compose -f docker-compose.yml -f docker-compose.test.yml up sonarqube"
fi
