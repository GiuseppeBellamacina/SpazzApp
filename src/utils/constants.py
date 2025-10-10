"""
Costanti e configurazioni del sistema SpazzApp.
"""

# Costanti per i giorni della settimana
GIORNI_SETTIMANA = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']

# Mesi in italiano
MESI_ITALIANI = [
    'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
    'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
]

# Stanze di default
STANZE_DEFAULT = ['Bagno', 'Cucina', 'Veranda', 'Corridoio']

# Persone di default
PERSONE_DEFAULT = ['Anna', 'Marco', 'Luca', 'Sofia']

# Configurazione PNG
PNG_CONFIG = {
    'DPI': 300,
    'LARGHEZZA': 16,
    'ALTEZZA': 9,
    'FONT_SIZE_TITOLO': 16,
    'FONT_SIZE_HEADER': 14,
    'FONT_SIZE_CELLA': 11,
    'COLORE_HEADER': '#2c3e50',
    'COLORE_BORDO': '#34495e',
    'COLORE_SFONDO': 'white',
    'COLORE_ALTERNATIVO': '#ecf0f1'
}

# CSS per Streamlit
CSS_STYLES = """
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .room-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .schedule-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 0.75rem;
        margin: 1rem 0;
    }
</style>
"""