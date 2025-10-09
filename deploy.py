#!/usr/bin/env python3
"""
Script di utilità per il deploy e la gestione dell'applicazione
"""

import subprocess
import sys
import os

def install_requirements():
    """Installa le dipendenze"""
    print("📦 Installando le dipendenze...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dipendenze installate!")

def run_app():
    """Avvia l'applicazione Streamlit"""
    print("🚀 Avviando l'applicazione...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

def main():
    """Funzione principale"""
    print("🏠 Gestione Turni Pulizie - Utility Script")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "install":
            install_requirements()
        elif command == "run":
            run_app()
        elif command == "setup":
            install_requirements()
            print("\n🎉 Setup completato! Ora puoi avviare l'app con: python deploy.py run")
        else:
            print(f"❌ Comando sconosciuto: {command}")
            print("Comandi disponibili: install, run, setup")
    else:
        print("Comandi disponibili:")
        print("  python deploy.py install  # Installa dipendenze")
        print("  python deploy.py run      # Avvia l'applicazione")
        print("  python deploy.py setup    # Setup completo")

if __name__ == "__main__":
    main()