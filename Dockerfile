FROM python:3.14-slim

# Logs de Python sin buffer (visibles en `docker logs` en tiempo real)
ENV PYTHONUNBUFFERED=1
# `uv run` no debe re-sincronizar al arrancar (instalaría el grupo dev, ej. pytest)
ENV UV_NO_SYNC=1

WORKDIR /app

# Instalar curl y limpiar cache
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv para gestión de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copiar archivos de configuración (incluido el lockfile para builds reproducibles)
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .

# Instalar dependencias exactamente como en el lockfile
RUN uv sync --no-dev --frozen

# Copiar esquema de base de datos y código fuente
COPY db.sql ./db.sql
COPY src/ ./src/

# Cambiar al directorio src para ejecutar la aplicación
WORKDIR /app/src
# Exponer puerto para FastAPI
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
