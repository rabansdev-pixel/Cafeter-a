# ==============================================================================
# Multi-Stage Dockerfile para Cafetería de Especialidad
# Targets: base, development, testing, production
# ==============================================================================

# --- Etapa Base Común ---
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# Crear usuario seguro no-root para producción y tests
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Copiar el archivo único de requerimientos
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# --- Etapa de Desarrollo ---
FROM base AS development
ENV APP_ENV=development \
    FLASK_DEBUG=1

COPY . /app
RUN chown -R appuser:appuser /app

EXPOSE 5000
CMD ["python", "run.py"]

# --- Etapa de Testing (Pytest + Coverage para SonarQube) ---
FROM base AS testing
ENV APP_ENV=testing

COPY . /app
RUN chown -R appuser:appuser /app
USER appuser

# Ejecuta suite de tests y genera reporte XML para SonarQube
CMD ["pytest", "tests/", "--cov=app", "--cov-report=xml:coverage.xml", "--cov-report=term-missing"]

# --- Etapa de Producción Endurecida ---
FROM base AS production
ENV APP_ENV=production \
    PORT=5000

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=appuser:appuser . /app

USER appuser
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--threads", "2", "--access-logfile", "-", "run:app"]
