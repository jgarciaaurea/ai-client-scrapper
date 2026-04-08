
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import os

# Ajustar path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import extract_nifs, setup_logger
from src.scraper import deep_extract_from_website

logger = setup_logger()

def test_ipcastro():
    url = "https://www.ipcastro.com/"
    print(f"\n🚀 PROBANDO CASO ESPECÍFICO: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            results = deep_extract_from_website(page, url)
            print(f"\n--- RESULTADOS FINALES ---")
            print(f"✅ CIF Extraído: {results['nif']}")
            print(f"✅ Email Extraído: {results['email']}")
            
            if results['nif'] == "A20156220":
                print("\n🎉 ¡ÉXITO! El sistema ha priorizado el CIF del Aviso Legal correctamente.")
            else:
                print(f"\n❌ FALLO. Se ha extraído {results['nif']} en lugar de A20156220.")
                
        except Exception as e:
            print(f"❌ Error durante la prueba: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_ipcastro()
