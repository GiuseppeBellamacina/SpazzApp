"""
Pagina di generazione e visualizzazione turni per SpazzApp.
"""

import streamlit as st

from src.ui.components import ScheduleDisplayManager
from src.utils.constants import CSS_STYLES, MESI_ITALIANI


def show_turni_page():
    """Mostra la pagina di generazione e visualizzazione turni."""
    st.markdown('<div class="main-header">🎲 Generazione Turni</div>', unsafe_allow_html=True)
    
    # Verifica che la configurazione sia presente
    if 'config' not in st.session_state or 'scheduler' not in st.session_state:
        st.error("❌ Configurazione non trovata! Vai alla pagina Configurazione.")
        if st.button("🔙 Torna alla Configurazione"):
            st.switch_page("pages/configurazione.py")
        return
    
    config = st.session_state.config
    scheduler = st.session_state.scheduler
    italian_months = {i: month for i, month in enumerate(MESI_ITALIANI, 1)}
    
    # Mostra riassunto configurazione
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Persone", len(config['people']))
    with col2:
        st.metric("🏠 Stanze", len(scheduler.rooms))
    with col3:
        month_name = italian_months[config['month']]
        st.metric("📅 Periodo", f"{month_name} {config['year']}")
    
    st.markdown("---")
    
    # Pulsanti di controllo
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("🔙 Modifica Configurazione"):
            st.switch_page("pages/configurazione.py")
    
    with col2:
        generate_button = st.button("🎲 Genera Nuovi Turni", type="primary", width="stretch")
    
    with col3:
        if 'schedule_df' in st.session_state:
            if st.button("📸 Vai all'Export"):
                st.switch_page("pages/export.py")
    
    # Genera turni
    if generate_button or st.button("🔄 Rigenera Turni"):
        _generate_and_display_schedule(config, scheduler, italian_months)
    elif 'schedule_df' in st.session_state:
        # Mostra turni già generati
        display_manager = ScheduleDisplayManager()
        display_manager.display_schedule(
            st.session_state.schedule_df, 
            scheduler.rooms, 
            italian_months,
            config['month'], 
            config['year']
        )
        
        # Mostra statistiche distribuzione
        _show_distribution_stats(st.session_state.schedule_df, config['people'])
        
        # Mostra pulsante per l'export
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📸 Vai all'Export PNG", type="secondary", width="stretch"):
                st.switch_page("pages/export.py")


def _show_distribution_stats(schedule_df, people):
    """Mostra statistiche di distribuzione per verificare l'equità."""
    st.markdown("---")
    st.subheader("📊 Controllo Distribuzione e Rotazione")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**👥 Distribuzione per Persona:**")
        person_stats = schedule_df['Persona'].value_counts()
        if "Nessuno disponibile" in person_stats.index:
            person_stats = person_stats.drop("Nessuno disponibile")
        
        # Verifica equità
        if len(person_stats) > 0:
            min_assignments = person_stats.min()
            max_assignments = person_stats.max()
            is_balanced = (max_assignments - min_assignments) <= 1
            
            for person in people:
                if person in person_stats.index:
                    count = person_stats[person]
                    if is_balanced:
                        st.write(f"• {person}: {count} stanze ✅")
                    else:
                        if count == min_assignments:
                            st.write(f"• {person}: {count} stanze ⚠️ (sotto la media)")
                        elif count == max_assignments:
                            st.write(f"• {person}: {count} stanze ⚠️ (sopra la media)")
                        else:
                            st.write(f"• {person}: {count} stanze")
                else:
                    st.write(f"• {person}: 0 stanze ❌")
            
            if is_balanced:
                st.success("✅ Distribuzione bilanciata tra persone!")
            else:
                st.warning(f"⚠️ Distribuzione sbilanciata: {min_assignments}-{max_assignments} stanze per persona")
    
    with col2:
        st.markdown("**📅 Distribuzione per Giorno:**")
        day_stats = schedule_df['Giorno_Settimana'].value_counts()
        giorni_ordine = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        
        # Calcola ideale (dovrebbe essere circa 4 stanze / 7 giorni per settimana)
        total_assignments = len(schedule_df)
        days_with_assignments = len([day for day in giorni_ordine if day in day_stats.index and day_stats[day] > 0])
        
        concentrated_days = 0
        for giorno in giorni_ordine:
            if giorno in day_stats.index:
                count = day_stats[giorno]
                if count > 1:
                    concentrated_days += 1
                    st.write(f"• {giorno}: {count} stanze ⚠️")
                else:
                    st.write(f"• {giorno}: {count} stanza ✅")
            else:
                st.write(f"• {giorno}: 0 stanze")
        
        if concentrated_days <= 1:
            st.success("✅ Buona distribuzione nei giorni!")
        else:
            st.warning(f"⚠️ {concentrated_days} giorni con multiple assegnazioni")
    
    with col3:
        st.markdown("**🔄 Rotazione Settimanale:**")
        
        # Analizza rotazione per persona
        rotation_analysis = {}
        for person in people:
            person_data = schedule_df[schedule_df['Persona'] == person]
            if len(person_data) > 0:
                unique_rooms = person_data['Stanza'].unique()
                total_assignments = len(person_data)
                rotation_analysis[person] = {
                    'rooms': list(unique_rooms),
                    'count': total_assignments,
                    'diversity': len(unique_rooms)
                }
        
        all_rooms = schedule_df['Stanza'].unique()
        max_diversity = len(all_rooms)
        
        good_rotation_count = 0
        for person, data in rotation_analysis.items():
            diversity_ratio = data['diversity'] / max_diversity
            if diversity_ratio >= 0.75:  # Ha fatto almeno 75% delle stanze diverse
                st.write(f"• {person}: {data['diversity']}/{max_diversity} stanze ✅")
                good_rotation_count += 1
            elif diversity_ratio >= 0.5:
                st.write(f"• {person}: {data['diversity']}/{max_diversity} stanze ⚠️")
            else:
                st.write(f"• {person}: {data['diversity']}/{max_diversity} stanze ❌")
                st.write(f"  Ripete: {', '.join(data['rooms'])}")
        
        if good_rotation_count == len(people):
            st.success("✅ Ottima rotazione settimanale!")
        elif good_rotation_count >= len(people) * 0.7:
            st.info("🔄 Rotazione accettabile")
        else:
            st.warning("⚠️ Rotazione insufficiente - alcune persone ripetono troppe volte le stesse stanze")


def _generate_and_display_schedule(config: dict, scheduler, italian_months: dict):
    """Genera e visualizza il piano dei turni."""
    with st.spinner("Generando i turni..."):
        schedule_df = scheduler.generate_schedule(
            config['people'], 
            config['year'], 
            config['month'], 
            config['absences'],
            config['excluded_first_week'],
            config['priority_first_week']
        )
    
    # Salva nel session_state per persistenza
    st.session_state.schedule_df = schedule_df
    
    st.success("✅ Turni generati con successo!")
    
    # Visualizza il piano
    display_manager = ScheduleDisplayManager()
    display_manager.display_schedule(
        schedule_df, 
        scheduler.rooms, 
        italian_months,
        config['month'], 
        config['year']
    )
    
    # Mostra statistiche distribuzione
    _show_distribution_stats(schedule_df, config['people'])
    
    # Mostra pulsante per l'export
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📸 Vai all'Export PNG", type="secondary", width="stretch"):
            st.switch_page("pages/export.py")


# Applicazione CSS
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Mostra la pagina
show_turni_page()