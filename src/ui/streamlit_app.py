"""
Applicazione Streamlit principale per SpazzApp.
"""

import streamlit as st
from datetime import datetime
import pandas as pd

from ..core.scheduler import CleaningScheduler
from ..ui.components import SidebarManager, ScheduleDisplayManager
from ..ui.image_generator import CalendarImageGenerator
from ..utils.constants import CSS_STYLES, MESI_ITALIANI


class StreamlitApp:
    """Classe principale dell'applicazione Streamlit."""
    
    def __init__(self):
        """Inizializza l'applicazione."""
        self.scheduler = CleaningScheduler()
        self.sidebar_manager = SidebarManager()
        self.display_manager = ScheduleDisplayManager()
        self.image_generator = CalendarImageGenerator()
        self.italian_months = {i: month for i, month in enumerate(MESI_ITALIANI, 1)}
    
    def configure_page(self):
        """Configura la pagina Streamlit."""
        st.set_page_config(
            page_title="🏠 SpazzApp",
            page_icon="🧹",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Applica stili CSS personalizzati
        st.markdown(CSS_STYLES, unsafe_allow_html=True)
    
    def run(self):
        """Esegue l'applicazione principale."""
        # Header
        st.markdown('<div class="main-header">🏠 SpazzApp 🧹</div>', unsafe_allow_html=True)
        
        # Configurazione dalla sidebar
        config = self.sidebar_manager.render_sidebar_configuration(self.scheduler.rooms)
        
        # Verifica validità configurazione
        if len(config['people']) < 2:
            st.warning("⚠️ Inserisci almeno 2 persone per generare i turni!")
            return
        
        # Genera turni
        if st.button("🎲 Genera Turni", type="primary", use_container_width=True):
            self._generate_and_display_schedule(config)
    
    def _generate_and_display_schedule(self, config: dict):
        """Genera e visualizza il piano dei turni."""
        with st.spinner("Generando i turni..."):
            schedule_df = self.scheduler.generate_schedule(
                config['people'], 
                config['year'], 
                config['month'], 
                config['absences'],
                config['excluded_first_week'],
                config['priority_first_week']
            )
        
        st.success("✅ Turni generati con successo!")
        
        # Visualizza il piano
        self.display_manager.display_schedule(
            schedule_df, 
            self.scheduler.rooms, 
            self.italian_months,
            config['month'], 
            config['year']
        )
        
        # Sezione export PNG
        self._render_png_export_section(schedule_df, config['month'], config['year'])
    
    def _render_png_export_section(self, schedule_df: pd.DataFrame, month: int, year: int):
        """Renderizza la sezione per l'export PNG."""
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Esporta PNG
            with st.spinner("Generando immagine del piano..."):
                try:
                    img_buffer = self.image_generator.create_calendar_image(
                        schedule_df, month, year
                    )
                    st.download_button(
                        label="🖼️ Scarica Piano Turni (PNG)",
                        data=img_buffer.getvalue(),
                        file_name=f"piano_turni_{self.italian_months[month]}_{year}.png",
                        mime="image/png",
                        use_container_width=True,
                        type="primary"
                    )
                    st.success("📸 Immagine pronta per il download!")
                except Exception as e:
                    st.error(f"Errore nella generazione dell'immagine: {str(e)}")
                    st.info("💡 Assicurati che le librerie matplotlib e pillow siano installate")


def create_app() -> StreamlitApp:
    """
    Factory function per creare l'applicazione.
    
    Returns:
        Istanza dell'applicazione Streamlit
    """
    app = StreamlitApp()
    app.configure_page()
    return app