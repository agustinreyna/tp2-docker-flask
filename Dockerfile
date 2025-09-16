# Imagen base oficial, liviana
FROM python:3.12-slim

# Variables para que Python no genere .pyc y loguee en stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias y instalarlas
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la app
COPY app/ .

# Exponer el puerto
EXPOSE 5000

# Comando por defecto
CMD ["python", "app.py"]
