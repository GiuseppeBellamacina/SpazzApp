"""
Pagina di export PNG per SpazzApp.
"""

import streamlit as st
from src.ui.image_generator import CalendarImageGenerator
from src.utils.constants import CSS_STYLES, MESI_ITALIANI


def show_export_page():
    """Mostra la pagina di export PNG."""
    st.markdown('<div class="main-header">📸 Export PNG</div>', unsafe_allow_html=True)
    
    # Verifica che i turni siano stati generati
    if 'schedule_df' not in st.session_state or 'config' not in st.session_state:
        st.error("❌ Nessun piano turni trovato! Genera prima i turni.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔙 Torna alla Configurazione"):
                st.switch_page("pages/configurazione.py")
        with col2:
            if st.button("🎲 Vai ai Turni"):
                st.switch_page("pages/turni.py")
        return
    
    schedule_df = st.session_state.schedule_df
    config = st.session_state.config
    italian_months = {i: month for i, month in enumerate(MESI_ITALIANI, 1)}
    
    # Informazioni sul piano
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Persone", len(config['people']))
    with col2:
        st.metric("🏠 Stanze", len(st.session_state.scheduler.rooms))
    with col3:
        month_name = italian_months[config['month']]
        st.metric("📅 Periodo", f"{month_name} {config['year']}")
    
    st.markdown("---")
    
    # Sezione export
    st.subheader("🖼️ Genera Immagine PNG")
    st.info("💡 L'immagine includerà tutto il piano dei turni in formato calendario")
    
    # Pulsanti di controllo
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("🔙 Torna ai Turni"):
            st.switch_page("pages/turni.py")
    
    with col2:
        # Genera e scarica PNG
        image_generator = CalendarImageGenerator()
        
        try:
            with st.spinner("Generando immagine del piano..."):
                img_buffer = image_generator.create_calendar_image(
                    schedule_df, config['month'], config['year']
                )
            
            # Mostra preview (opzionale)
            if st.checkbox("🔍 Mostra Anteprima", value=False):
                st.image(img_buffer.getvalue(), caption="Anteprima Piano Turni", width="stretch")
            
            # Pulsante download
            download_button = st.download_button(
                label="🖼️ Scarica Piano Turni (PNG)",
                data=img_buffer.getvalue(),
                file_name=f"piano_turni_{italian_months[config['month']]}_{config['year']}.png",
                mime="image/png",
                width="stretch",
                type="primary"
            )
            
            if download_button:
                st.success("📸 Immagine scaricata con successo!")
                
                # Mantieni stato senza ricaricare la pagina
                st.info("✅ Puoi continuare a usare l'app senza perdere i dati!")
                
        except Exception as e:
            st.error(f"❌ Errore nella generazione dell'immagine: {str(e)}")
            st.info("💡 Assicurati che le librerie matplotlib e pillow siano installate")
    
    with col3:
        if st.button("🎲 Rigenera Turni"):
            st.switch_page("pages/turni.py")
    
    st.markdown("---")
    
    # Statistiche del piano
    st.subheader("📊 Statistiche Piano")
    
    # Conta assegnazioni per persona
    person_assignments = schedule_df['Persona'].value_counts()
    if "Nessuno disponibile" in person_assignments.index:
        person_assignments = person_assignments.drop("Nessuno disponibile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Assegnazioni per Persona:**")
        for person, count in person_assignments.items():
            st.write(f"• {person}: {count} stanze")
    
    with col2:
        st.write("**Distribuzione per Giorno:**")
        day_stats = schedule_df['Giorno_Settimana'].value_counts()
        giorni_ordine = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        
        for giorno in giorni_ordine:
            if giorno in day_stats.index:
                count = day_stats[giorno]
                # Indica se il giorno ha troppe assegnazioni
                if count > 1:
                    st.write(f"• {giorno}: {count} stanze ⚠️")
                else:
                    st.write(f"• {giorno}: {count} stanza ✅")
            else:
                st.write(f"• {giorno}: 0 stanze")
        
        # Statistiche per settimana
        st.write("**Stanze per Settimana:**")
        week_stats = schedule_df.groupby('Settimana')['Stanza'].count()
        for week, count in week_stats.items():
            st.write(f"• {week}: {count} stanze")


# Applicazione CSS
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Mostra la pagina
show_export_page()