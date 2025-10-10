"""
SpazzApp - Gestione Turni di Pulizia Intelligente
Applicazione multipagina con Streamlit per la gestione intelligente dei turni di pulizia.
"""

import streamlit as st
from src.utils.constants import CSS_STYLES

# Configurazione della pagina principale
st.set_page_config(
    page_title="🏠 SpazzApp", 
    page_icon="🧹", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Applicazione stili CSS
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Configurazione delle pagine
pages = {
    "🏠 SpazzApp": [
        st.Page("pages/configurazione.py", title="Configurazione", icon="⚙️"),
        st.Page("pages/turni.py", title="Generazione Turni", icon="🎲"),
        st.Page("pages/export.py", title="Export PNG", icon="📸")
    ]
}

# Navigazione
pg = st.navigation(pages)
pg.run()
