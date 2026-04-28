# ai-client-scrapper

Scraper automatizado de empresas del sector seleccionado, con enriquecimiento de subvenciones y panel de control web.

---

## Características Principales

- **Panel de Control Web**: Interfaz visual con Streamlit para gestionar todo el proceso sin comandos.
- **Buscador en Tiempo Real**: Lanza búsquedas y ve cómo aparecen los leads y sus subvenciones.
- **Enriquecimiento BDNS**: Consulta automática de subvenciones en la API de Hacienda (BDNS).
- **Email Marketing Controlado**: Envío manual o automático de propuestas personalizadas.
- **Editor de Plantillas**: Modifica el email comercial directamente desde la web.
- **Dockerizado**: Despliegue sencillo en cualquier servidor Linux.

---

## Interfaz Web (Dashboard)

Al desplegar el proyecto, tendrás acceso a una web en el puerto `8501` con:
1.  **Dashboard**: Métricas de leads, subvenciones y contactos.
2.  **Buscador**: Configura la palabra clave y lanza el scraper.
3.  **Tabla de Leads**: Filtra por importe de subvención, NIF o prioridad.
4.  **Acciones**: Botón para enviar emails individuales tras revisar el lead.
5.  **Editor**: Previsualización y edición de la plantilla HTML del email.

---

## Estructura del Proyecto

```
ai-client-scrapper/
├── src/
│   ├── app.py            # Interfaz Web (Streamlit)
│   ├── scraper.py        # Motor de extracción
│   ├── enrich_leads.py   # Validador de subvenciones
│   ├── mailer.py         # Motor de envío SMTP
│   └── models.py         # Base de datos (SQLAlchemy)
├── templates/
│   └── email_comercial.html # Plantilla personalizable
├── data/                 # Base de datos (Persistente)
├── Dockerfile            # Imagen de producción
└── docker-compose.yml    # Orquestación
```

---

## Despliegue en Servidor Propio (Ubuntu)

### 1. Clonar y Configurar
```bash
git clone https://github.com/jgarciaaurea/ai-client-scrapper.git
cd ai-client-scrapper
cp .env.example .env
nano .env # Configura tu SMTP y ajustes
```

### 2. Levantar con Docker
```bash
docker-compose build
docker-compose up -d
```

### 3. Acceder a la Web
Abre tu navegador en: `http://tu-ip-servidor:8501`

---

## Notas Técnicas y Seguridad

- **Persistencia**: La base de datos `leads.db` se guarda en la carpeta `./data` de tu servidor. No se borra al reiniciar el contenedor.
- **Seguridad**: El acceso web no tiene contraseña por defecto. Se recomienda cerrar el puerto 8501 al público o usar un túnel SSH/VPN para acceder.
- **Anti-bloqueo**: El sistema usa rotación de User-Agents y pausas inteligentes para evitar ser detectado por los directorios.

---

## Licencia

MIT License — uso libre con atribución.
