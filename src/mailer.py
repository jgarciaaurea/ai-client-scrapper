"""
mailer.py
---------
Módulo para el envío automatizado de emails comerciales utilizando SMTP y plantillas Jinja2.
"""

import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# Añadir el directorio raíz al path para importar módulos locales
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models import init_db, Lead
from src.utils import setup_logger

# Cargar variables de entorno
load_dotenv(PROJECT_ROOT / ".env")

# Configuración de logs
LOG_DIR = os.getenv("LOG_DIR", "logs")
logger = setup_logger(LOG_DIR)

# Configuración SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/leads.db")

# Configuración de Jinja2
env = Environment(loader=FileSystemLoader(str(PROJECT_ROOT / "templates")))


def send_email(to_email, subject, body):
    """Envía un email individual vía SMTP."""
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASS]):
        logger.error("Configuración SMTP incompleta en .env. Saltando envío.")
        return False

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Error enviando email a {to_email}: {e}")
        return False


def process_mail_queue():
    """Selecciona leads cualificados y envía el email comercial."""
    logger.info("=" * 60)
    logger.info("Iniciando proceso de envío de emails comerciales")
    logger.info("=" * 60)

    session = init_db(DATABASE_URL)
    
    # Seleccionar leads con subvenciones, con email y no contactados
    leads_to_contact = (
        session.query(Lead)
        .filter(Lead.total_subvenciones > 0)
        .filter(Lead.email.isnot(None))
        .filter(Lead.contactado == False)
        .all()
    )

    if not leads_to_contact:
        logger.info("No hay nuevos leads cualificados para contactar.")
        session.close()
        return

    logger.info(f"Se han encontrado {len(leads_to_contact)} leads para contactar.")
    
    template = env.get_template("email_comercial.html")
    sent_count = 0

    for lead in leads_to_contact:
        logger.info(f"Preparando email para: {lead.nombre} ({lead.email})")
        
        # Generar cuerpo del mensaje
        html_content = template.render(
            nombre_empresa=lead.nombre,
            total_subvenciones=f"{lead.total_subvenciones:,.2f}"
        )
        
        subject = f"Oportunidad de crecimiento para {lead.nombre} - Sector Solar"
        
        # Simulación o envío real
        if os.getenv("DRY_RUN", "false").lower() == "true":
            logger.info(f"[DRY RUN] Email generado correctamente para {lead.email}")
            lead.contactado = True
            sent_count += 1
        else:
            if send_email(lead.email, subject, html_content):
                logger.info(f"Email enviado con éxito a {lead.email}")
                lead.contactado = True
                sent_count += 1
            else:
                logger.warning(f"No se pudo enviar el email a {lead.email}")

    try:
        session.commit()
        logger.info(f"Proceso finalizado. Emails enviados: {sent_count}")
    except Exception as e:
        logger.error(f"Error al actualizar estado de contacto: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    process_mail_queue()
