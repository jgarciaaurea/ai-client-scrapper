"""
scraper.py
----------
Script principal de scraping con navegación profunda y prioridad legal.
"""

import os
import re
import sys
import time
import random
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse, urlunparse, parse_qs

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

# Ajustar path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import init_db
from src.utils import (
    setup_logger, save_lead, export_to_csv, clean_text, 
    extract_emails, extract_nifs, normalize_url, validate_spanish_id
)

# ─────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

KEYWORD = os.getenv("SEARCH_KEYWORD", "instalaciones solares")
MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/leads.db")
LOG_DIR = os.getenv("LOG_DIR", "logs")
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"

PROJECT_ROOT = Path(__file__).parent.parent
db_path_raw = DATABASE_URL.replace("sqlite:///", "")
if not Path(db_path_raw).is_absolute():
    DATABASE_URL = f"sqlite:///{PROJECT_ROOT / db_path_raw}"
LOG_DIR = str(PROJECT_ROOT / LOG_DIR)

logger = setup_logger(LOG_DIR)


# ─────────────────────────────────────────────
# Helpers de Navegación Profunda
# ─────────────────────────────────────────────

LEGAL_KEYWORDS = ["aviso legal", "legal notice", "privacidad", "privacy", "rgpd", "lopd", "quienes somos"]
CONTACT_KEYWORDS = ["contacto", "contact"]

def random_delay(min_s: float = 1.0, max_s: float = 2.0) -> None:
    time.sleep(random.uniform(min_s, max_s))


def deep_extract_from_website(page: Page, web_url: str) -> Dict[str, Optional[str]]:
    """
    Navega por la web buscando NIF y Email con prioridad absoluta a páginas legales.
    """
    results = {"email": None, "nif": None}
    if not web_url or not web_url.startswith("http"):
        return results

    try:
        # 1. Visitar Home
        logger.debug(f"Deep Scraping Home: {web_url}")
        page.goto(web_url, timeout=15_000, wait_until="domcontentloaded")
        random_delay(0.5, 1.0)
        html_home = page.content()
        
        emails_home = extract_emails(html_home)
        nifs_home = extract_nifs(html_home)
        
        if emails_home: results["email"] = emails_home[0]
        if nifs_home: results["nif"] = nifs_home[0]

        # 2. Buscar enlaces legales y de contacto
        all_links = page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a'));
                return links.map(a => ({
                    text: a.innerText.toLowerCase(),
                    href: a.href
                })).filter(l => l.href && l.href.startsWith('http'));
            }
        """)
        
        legal_links = [l['href'] for l in all_links if any(k in l['text'] for k in LEGAL_KEYWORDS)]
        contact_links = [l['href'] for l in all_links if any(k in l['text'] for k in CONTACT_KEYWORDS)]
        
        # Prioridad 1: Aviso Legal (Máxima fiabilidad para CIF)
        for link in set(legal_links[:2]):
            try:
                logger.debug(f"Deep Scraping Legal: {link}")
                page.goto(link, timeout=10_000, wait_until="domcontentloaded")
                random_delay(0.5, 1.0)
                html_legal = page.content()
                
                nifs_legal = extract_nifs(html_legal)
                emails_legal = extract_emails(html_legal)
                
                # Sobrescribimos si encontramos algo en el Aviso Legal (es más fiable)
                if nifs_legal: 
                    results["nif"] = nifs_legal[0]
                    logger.debug(f"NIF encontrado en página legal: {results['nif']}")
                if emails_legal: results["email"] = emails_legal[0]
                
                if results["nif"]: break # Si ya tenemos NIF de aviso legal, paramos
            except:
                continue

        # Prioridad 2: Contacto (Fiabilidad para Email)
        if not results["email"]:
            for link in set(contact_links[:2]):
                try:
                    logger.debug(f"Deep Scraping Contact: {link}")
                    page.goto(link, timeout=10_000, wait_until="domcontentloaded")
                    random_delay(0.5, 1.0)
                    html_contact = page.content()
                    emails_contact = extract_emails(html_contact)
                    if emails_contact:
                        results["email"] = emails_contact[0]
                        break
                except:
                    continue

    except Exception as exc:
        logger.debug(f"Error en deep_extract '{web_url}': {exc}")
    
    return results


# ─────────────────────────────────────────────
# Scrapers por Fuente
# ─────────────────────────────────────────────

def scrape_paginas_amarillas(page: Page, session, keyword: str, max_pages: int) -> int:
    source = "Páginas Amarillas"
    keyword_slug = keyword.replace(" ", "-").lower()
    raw_leads = []

    for page_num in range(1, max_pages + 1):
        url = f"https://www.paginasamarillas.es/search/{keyword_slug}/all-ma/all-pr/all-is/all-ci/all-ba/all-pu/all-nc/{page_num}?what={keyword.replace(' ', '+')}&qc=true"
        logger.info(f"[{source}] Listado página {page_num}")

        try:
            page.goto(url, timeout=25_000, wait_until="domcontentloaded")
            random_delay(1, 2)
            card_selector = "div.listado-item, article.advert-item, div[id^='advert-']"
            page.wait_for_selector(card_selector, timeout=10_000)
            
            cards = page.evaluate("""
                () => {
                    const items = document.querySelectorAll('div.listado-item, article.advert-item, div[id^="advert-"]');
                    return Array.from(items).map(card => {
                        const h2 = card.querySelector('h2, .business-name, a[title]');
                        const webEl = card.querySelector('a.web, a[href*="http"]:not([href*="paginasamarillas"])');
                        return {
                            nombre: h2 ? h2.innerText.replace('+info','').trim() : '',
                            web: webEl ? webEl.href : ''
                        };
                    }).filter(d => d.nombre.length > 2);
                }
            """)
            raw_leads.extend(cards)
            if not page.query_selector('a[rel="next"], .pagination-next'): break
        except Exception as e:
            logger.warning(f"[{source}] Error en página {page_num}: {e}")
            break

    total_saved = 0
    unique_raw = {d['nombre']: d for d in raw_leads}.values()
    
    for data in unique_raw:
        web_url = normalize_url(data.get("web"))
        deep_data = {"email": None, "nif": None}
        if web_url:
            deep_data = deep_extract_from_website(page, web_url)
        
        lead_final = {
            "nombre": data["nombre"],
            "web": web_url,
            "email": deep_data["email"],
            "nif": deep_data["nif"],
            "fuente": source,
            "keyword": keyword
        }
        if save_lead(session, lead_final, logger):
            total_saved += 1
    return total_saved


def run_all_scrapers():
    logger.info("="*60)
    logger.info(f"INICIANDO SCRAPER CON PRIORIDAD LEGAL - KEYWORD: {KEYWORD}")
    logger.info("="*60)
    session = init_db(DATABASE_URL)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = context.new_page()
        try:
            count = scrape_paginas_amarillas(page, session, KEYWORD, MAX_PAGES)
            logger.info(f"Proceso finalizado. Total leads guardados/actualizados: {count}")
        finally:
            browser.close()
    export_to_csv(session, str(PROJECT_ROOT / "data" / "leads.csv"), logger)
    session.close()

if __name__ == "__main__":
    run_all_scrapers()
