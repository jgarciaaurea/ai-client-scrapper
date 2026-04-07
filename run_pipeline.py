"""
run_pipeline.py
---------------
Orquestador principal del proyecto ai-client-scrapper.
Ejecuta el pipeline completo:
1. Scraper (obtención de leads)
2. Enriquecimiento BDNS (validación de subvenciones)
3. Mailer (envío de emails comerciales)
"""

import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Configuración básica
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

def run_script(script_path, env_vars=None):
    """Ejecuta un script de Python como subproceso."""
    print(f"\n>>> Ejecutando: {script_path}")
    
    current_env = os.environ.copy()
    if env_vars:
        current_env.update(env_vars)
        
    try:
        # Usamos sys.executable para asegurar que usamos el mismo intérprete de Python
        result = subprocess.run(
            [sys.executable, str(script_path)],
            env=current_env,
            check=True,
            capture_output=False, # Mostrar salida en tiempo real
            text=True
        )
        print(f">>> {script_path} completado con éxito.")
        return True
    except subprocess.CalledProcessError as e:
        print(f">>> ERROR al ejecutar {script_path}: {e}")
        return False

def main():
    print("=" * 60)
    print("INICIANDO PIPELINE DE AI CLIENT SCRAPPER")
    print("=" * 60)
    
    # 1. Ejecutar el Scraper
    # Limitamos a 1 página por defecto en el orquestador para evitar bloqueos excesivos
    if not run_script(PROJECT_ROOT / "src" / "scraper.py", {"MAX_PAGES": "1"}):
        print("Pipeline detenido por error en el Scraper.")
        return

    # 2. Ejecutar el Enriquecimiento BDNS
    if not run_script(PROJECT_ROOT / "src" / "enrich_leads.py"):
        print("Pipeline detenido por error en el Enriquecimiento BDNS.")
        return

    # 3. Ejecutar el Mailer
    # Nota: Si no hay configuración SMTP en .env, el mailer registrará el error y continuará
    if not run_script(PROJECT_ROOT / "src" / "mailer.py"):
        print("Pipeline finalizado con advertencias en el Mailer.")
    else:
        print("Pipeline completado con éxito.")
        
    print("\n" + "=" * 60)
    print("PROCESO FINALIZADO")
    print("=" * 60)

if __name__ == "__main__":
    main()
