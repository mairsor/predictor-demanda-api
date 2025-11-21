# Dockerfile para el Sistema de Predicción de Demanda de Matrícula
# Proyecto: Predicción de Demanda de Cursos (UNI)
# Última actualización: 2025-11-20

# Usar imagen base oficial de Python 3.11
FROM python:3.11-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorios necesarios si no existen
RUN mkdir -p data models results logs

# Exponer el puerto de la API
EXPOSE 8000

# Healthcheck para verificar que la API está respondiendo
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando por defecto para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
