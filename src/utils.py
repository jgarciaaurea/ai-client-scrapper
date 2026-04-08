"""
utils.py
--------
Utilidades compartidas: configuración de logging, limpieza de datos,
extracción avanzada con Regex y validación de algoritmo de control (CIF/NIF).
"""

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, List

import pandas as pd
from sqlalchemy.orm import Session

from src.models import Lead


# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────

def setup_logger(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    """Configura un logger con salida a consola y archivo rotativo."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = os.path.join(log_dir, "scraper.log")

    logger = logging.getLogger("ai_client_scrapper")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# ─────────────────────────────────────────────
# Validación de Algoritmo de Control (NIF/CIF)
# ─────────────────────────────────────────────

def validate_spanish_id(id_str: str) -> bool:
    """
    Valida el formato y el dígito de control de un NIF/CIF/NIE español.
    """
    id_str = id_str.upper().replace("-", "").replace(".", "").replace(" ", "")
    if len(id_str) != 9:
        return False

    # NIE: Cambiar X, Y, Z por 0, 1, 2
    nie_prefix = {"X": "0", "Y": "1", "Z": "2"}
    if id_str[0] in nie_prefix:
        temp_id = nie_prefix[id_str[0]] + id_str[1:]
    else:
        temp_id = id_str

    # Patrón NIF (Persona física): 8 números + 1 letra
    if re.match(r"^\d{8}[A-Z]$", temp_id):
        letras = "TRWAGMYFPDXBNJZSQVHLCKE"
        return letras[int(temp_id[:8]) % 23] == temp_id[8]

    # Patrón CIF (Persona jurídica): 1 letra + 7 números + 1 control (letra o número)
    if re.match(r"^[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]$", id_str):
        # Algoritmo de control CIF
        letter = id_str[0]
        digits = [int(d) for d in id_str[1:8]]
        
        # Suma de posiciones pares
        even_sum = digits[1] + digits[3] + digits[5]
        
        # Suma de posiciones impares multiplicadas por 2 (y sumando sus dígitos si > 9)
        odd_sum = 0
        for i in [0, 2, 4, 6]:
            prod = digits[i] * 2
            odd_sum += (prod // 10) + (prod % 10)
        
        total_sum = even_sum + odd_sum
        control_digit = (10 - (total_sum % 10)) % 10
        control_letter = "JABCDEFGHI"[control_digit]
        
        last_char = id_str[8]
        # Dependiendo de la letra inicial, el control puede ser letra, número o ambos
        if letter in "ABEH": # Solo número
            return last_char == str(control_digit)
        elif letter in "PQSW": # Solo letra
            return last_char == control_letter
        else: # Ambos válidos
            return last_char == str(control_digit) or last_char == control_letter

    return False


# ─────────────────────────────────────────────
# Extracción y Limpieza
# ─────────────────────────────────────────────

def clean_text(text: Optional[str]) -> Optional[str]:
    """Elimina espacios redundantes y caracteres de control."""
    if not text:
        return None
    return re.sub(r"\s+", " ", text.strip()) or None


def normalize_text_for_cif(text: str) -> str:
    """Normalización profunda para facilitar la detección de CIFs."""
    text = text.upper().replace("\xa0", " ")
    text = re.sub(r'(\d)\.(\d)', r'\1\2', text)
    text = re.sub(r'(\d)\s+(?=\d)', r'\1', text)
    text = re.sub(r'([A-Z])\s*[-—·\.]\s*(\d)', r'\1\2', text)
    text = re.sub(r'(\d)\s*[-—·\.]\s*([A-Z])', r'\1\2', text)
    return text


def extract_emails(text: Optional[str]) -> List[str]:
    """Extrae todos los emails únicos encontrados en un texto."""
    if not text:
        return []
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    matches = re.findall(pattern, text)
    cleaned = [m.lower() for m in matches if not any(x in m.lower() for x in ['.png', '.jpg', '.js', '.css', 'example.com'])]
    return list(set(cleaned))


def extract_nifs(text: Optional[str]) -> List[str]:
    """Extrae NIFs/CIFs españoles únicos de un texto usando Regex y validación de algoritmo."""
    if not text:
        return []
    
    text_norm = normalize_text_for_cif(text)
    
    # Patrones específicos de CIF/NIF
    patterns = [
        r'(?:CIF|NIF|N\.I\.F\.|C\.I\.F\.|NIF/CIF)[:\s\-—·]*([A-Z0-9]{9})',
        r'\b([A-Z]\d{7}[0-9A-Z])\b',
        r'\b(\d{8}[A-Z])\b',
    ]
    
    found = []
    for pattern in patterns:
        matches = re.findall(pattern, text_norm)
        for m in matches:
            cif_clean = re.sub(r'[^\w]', '', str(m).upper())
            if len(cif_clean) == 9 and validate_spanish_id(cif_clean):
                found.append(cif_clean)
    
    return list(set(found))


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Asegura que la URL tenga esquema http/https."""
    if not url:
        return None
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url or None


# ─────────────────────────────────────────────
# Persistencia
# ─────────────────────────────────────────────

def save_lead(session: Session, lead_data: dict, logger: logging.Logger) -> bool:
    """Inserta o actualiza un lead en la base de datos."""
    nombre = lead_data.get("nombre", "").strip()
    fuente = lead_data.get("fuente", "desconocida")
    web = normalize_url(lead_data.get("web"))
    nif = lead_data.get("nif")
    email = lead_data.get("email")

    if not nombre or not (web or nif or email):
        return False

    existing = session.query(Lead).filter_by(nombre=nombre, fuente=fuente).first()
    if existing:
        updated = False
        if not existing.nif and nif:
            existing.nif = nif
            updated = True
        if not existing.email and email:
            existing.email = email
            updated = True
        if not existing.web and web:
            existing.web = web
            updated = True
        if updated:
            session.commit()
            logger.info(f"Lead actualizado: '{nombre}'")
        return False

    lead = Lead(
        nombre=nombre,
        web=web,
        nif=nif,
        email=email,
        fuente=fuente,
        keyword=lead_data.get("keyword"),
    )
    session.add(lead)
    try:
        session.commit()
        logger.info(f"Lead guardado: '{nombre}' | NIF={nif} | Email={email}")
        return True
    except Exception as exc:
        session.rollback()
        logger.error(f"Error al guardar lead '{nombre}': {exc}")
        return False


def export_to_csv(session: Session, output_path: str, logger: logging.Logger) -> None:
    """Exporta todos los leads a CSV."""
    leads = session.query(Lead).all()
    if not leads:
        return
    data = [lead.to_dict() for lead in leads]
    df = pd.DataFrame(data)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info(f"Exportados {len(df)} leads a '{output_path}'.")
