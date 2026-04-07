# Imagen base oficial de Python (slim para ligereza)
FROM python:3.10-slim

# Evitar generación de archivos .pyc y activar salida sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias de sistema necesarias para Playwright (Chromium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar solo el navegador Chromium de Playwright
RUN playwright install chromium

# Copiar el código del proyecto
COPY . .

# Crear directorios para datos y logs (para volúmenes de Docker)
RUN mkdir -p data logs

# Comando por defecto: ejecutar el orquestador
CMD ["python", "run_pipeline.py"]
