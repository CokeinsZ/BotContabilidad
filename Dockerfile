FROM python:3.14-slim

WORKDIR /app

# Instalar curl y limpiar cache
RUN apt-get update && apt-get install -y curl 

# Instalar uv para gestión de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copiar archivos de configuración
COPY pyproject.toml .
COPY README.md .

# Instalar dependencias
RUN uv sync --no-dev

# Copiar esquema de base de datos y código fuente
COPY db.sql ./db.sql
COPY src/ ./src/

# Directorio persistente para la base de datos SQLite
RUN mkdir -p /app/data

# Cambiar al directorio src para ejecutar la aplicación
WORKDIR /app/src
# Exponer puerto para FastAPI
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
