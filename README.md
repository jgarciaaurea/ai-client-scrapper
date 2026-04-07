# ai-client-scrapper

Scraper automatizado de empresas del sector de **instalaciones solares en España**, construido con [Playwright](https://playwright.dev/python/) y Python 3.10. Los resultados se persisten en una base de datos SQLite local (`leads.db`) y se exportan a CSV.

---

## Características

- **Pipeline Completo**: Scrapeo, Enriquecimiento de Subvenciones (BDNS) y Envío de Emails en un solo flujo.
- **Fuentes Sectoriales**: Páginas Amarillas, Empresite, UNEF Asociados, Kompass España.
- **Enriquecimiento de emails**: Visita la web de cada empresa para extraer el email de contacto.
- **Módulo de Subvenciones**: Consulta automática a la API de la BDNS (Hacienda) mediante NIF.
- **Marketing Automatizado**: Envío de emails comerciales personalizados con plantillas Jinja2.
- **Anti-bot**: Rotación de User-Agent y sesiones de navegador independientes.
- **Persistencia**: SQLite mediante SQLAlchemy ORM con volúmenes para Docker.

---

## Estructura del Proyecto

```
ai-client-scrapper/
├── src/
│   ├── scraper.py        # Extracción de leads
│   ├── enrich_leads.py   # Consulta de subvenciones (BDNS)
│   ├── mailer.py         # Envío de emails SMTP
│   ├── models.py         # Modelos de base de datos
│   └── utils.py          # Utilidades y logging
├── services/
│   └── bdns_service.py   # Integración con API de Hacienda
├── templates/
│   └── email_comercial.html # Plantilla de email Jinja2
├── data/                 # Base de datos y CSVs (Persistente)
├── logs/                 # Logs de ejecución (Persistente)
├── run_pipeline.py       # Orquestador principal
├── Dockerfile            # Configuración de contenedor
└── docker-compose.yml    # Orquestación de servicios
```

---

## Despliegue en Servidor Propio (Ubuntu)

Para poner en marcha el proyecto en tu propio servidor de forma rápida y barata usando Docker:

### 1. Preparación
```bash
# Clonar el repositorio
git clone https://github.com/jgarciaaurea/ai-client-scrapper.git
cd ai-client-scrapper

# Crear archivo de configuración
cp .env.example .env
```

### 2. Configuración
Edita el archivo `.env` con tus credenciales SMTP y ajustes de búsqueda:
```bash
nano .env
```

### 3. Construcción y Despliegue
```bash
# Construir la imagen de Docker
docker-compose build

# Ejecutar el pipeline completo
docker-compose up
```

### 4. Automatización (Opcional)
Para ejecutar el scraper automáticamente todos los lunes a las 08:00, añade una tarea a tu `crontab`:
```bash
crontab -e
# Añadir al final del archivo:
0 8 * * 1 cd /ruta/a/ai-client-scrapper && /usr/local/bin/docker-compose up >> /ruta/a/ai-client-scrapper/logs/cron.log 2>&1
```

---

## Variables de Entorno (.env)

| Variable | Descripción |
|---|---|
| `SEARCH_KEYWORD` | Palabra clave para el scraper |
| `MAX_PAGES` | Páginas a procesar por fuente |
| `SMTP_SERVER` | Servidor de correo (ej: smtp.gmail.com) |
| `SMTP_USER` | Tu usuario/email de envío |
| `SMTP_PASS` | Contraseña de aplicación |
| `DRY_RUN` | `true` para simular envíos, `false` para envío real |

---

## Notas Técnicas

- **Persistencia**: Los datos se guardan en la carpeta `./data` del host gracias al volumen configurado en `docker-compose.yml`.
- **Seguridad**: Nunca subas el archivo `.env` ni la base de datos `leads.db` a repositorios públicos.
- **Playwright**: El Dockerfile incluye todas las dependencias necesarias para ejecutar Chromium en Linux sin interfaz gráfica.

---

## Licencia

MIT License — uso libre con atribución.
