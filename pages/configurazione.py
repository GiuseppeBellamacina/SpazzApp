"""
Pagina di configurazione per SpazzApp.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Tuple
from src.core.scheduler import CleaningScheduler
from src.utils.constants import CSS_STYLES, MESI_ITALIANI, PERSONE_DEFAULT


def show_configuration_page():
    """Mostra la pagina di configurazione."""
    st.markdown('<div class="main-header">⚙️ Configurazione SpazzApp</div>', unsafe_allow_html=True)
    
    # Inizializza lo scheduler
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = CleaningScheduler()
    
    # Sidebar con informazioni di supporto
    render_info_sidebar()
    
    # Contenuto principale: configurazione vera e propria
    config = render_main_configuration()
    
    # Salva la configurazione nel session_state
    st.session_state.config = config
    
    # Riassunto configurazione finale
    st.markdown("---")
    st.subheader("📋 Riassunto Configurazione")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**👥 Persone configurate:**")
        if config['people']:
            for i, person in enumerate(config['people'], 1):
                st.write(f"{i}. {person}")
        else:
            st.write("❌ Nessuna persona configurata")
        
        st.markdown("**📅 Periodo selezionato:**")
        italian_months = {i: month for i, month in enumerate(MESI_ITALIANI, 1)}
        st.write(f"🗓️ {italian_months[config['month']]} {config['year']}")
    
    with col2:
        st.markdown("**🏠 Stanze da gestire:**")
        for i, room in enumerate(st.session_state.scheduler.rooms, 1):
            st.write(f"{i}. {room}")
        
        if config['absences']:
            st.markdown("**🚫 Assenze registrate:**")
            absence_count = sum(len(absence_list) for absence_list in config['absences'].values())
            if absence_count > 0:
                st.write(f"📊 {absence_count} periodo/i di assenza configurati")
                for person, absence_list in config['absences'].items():
                    if absence_list:
                        st.write(f"• **{person}**: {len(absence_list)} assenze")
            else:
                st.write("✅ Nessuna assenza configurata")
        else:
            st.write("✅ Nessuna assenza configurata")
    
    # Pulsante per procedere alla generazione
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if len(config['people']) >= 2:
            if st.button("➡️ Procedi alla Generazione Turni", type="primary", width="stretch"):
                st.switch_page("pages/turni.py")
        else:
            st.warning("⚠️ Inserisci almeno 2 persone per procedere alla generazione dei turni!")


def render_info_sidebar():
    """Renderizza la sidebar con informazioni di supporto."""
    st.sidebar.header("ℹ️ Guida alla Configurazione")
    
    st.sidebar.markdown("""
    ### 📋 Come configurare SpazzApp:
    
    **1. 👥 Coinquilini**
    - Inserisci almeno 2 persone
    - Un nome per riga
    - Evita caratteri speciali
    
    **2. 📅 Periodo**
    - Seleziona mese e anno
    - Il sistema genera turni per tutto il mese
    
    **3. 🚫 Assenze**
    - Aggiungi periodi di assenza
    - Specifica data inizio e fine
    - L'algoritmo eviterà quei giorni
    
    **4. ⚙️ Prima Settimana**
    - Personalizza esclusioni specifiche
    - Imposta priorità per le stanze
    """)
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("""
    ### 🏠 Stanze Gestite:
    - 🚿 **Bagno**: Pulizia completa
    - 🍳 **Cucina**: Superfici e pavimenti  
    - 🌿 **Veranda**: Spazzare e ordinare
    - 🚪 **Corridoio**: Aspirapolvere
    """)
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("""
    ### 🎯 Algoritmo Intelligente:
    - **Distribuzione equa**: Bilancia il carico tra persone
    - **Separazione giorni**: Evita sovrapposizioni quando possibile
    - **Gestione vincoli**: Rispetta assenze ed esclusioni
    - **Rotazione mensile**: Varia le assegnazioni nel tempo
    """)


def render_main_configuration():
    """Renderizza la configurazione principale nel contenuto."""
    
    # Sezione 1: Persone
    st.subheader("👥 Coinquilini")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        people_input = st.text_area(
            "Inserisci i nomi dei coinquilini (uno per riga):",
            value="\n".join(PERSONE_DEFAULT),
            height=120,
            help="Inserisci un nome per ogni riga. Minimo 2 persone richieste."
        )
        people = [name.strip() for name in people_input.split('\n') if name.strip()]
    
    with col2:
        st.markdown("**Preview:**")
        if people:
            for i, person in enumerate(people, 1):
                st.write(f"{i}. {person}")
        else:
            st.write("Nessuna persona inserita")
    
    st.markdown("---")
    
    # Sezione 2: Periodo
    st.subheader("📅 Periodo")
    italian_months = {i: month for i, month in enumerate(MESI_ITALIANI, 1)}
    
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox(
            "Mese:",
            range(1, 13),
            index=datetime.now().month - 1,
            format_func=lambda x: italian_months[x]
        )
    
    with col2:
        selected_year = st.selectbox(
            "Anno:",
            range(datetime.now().year, datetime.now().year + 2),
            index=0
        )
    
    st.markdown("---")
    
    # Sezione 3: Gestione Assenze
    st.subheader("🚫 Gestione Assenze")
    absences = render_absences_section(people, selected_year, selected_month)
    
    st.markdown("---")
    
    # Sezione 4: Configurazione Prima Settimana
    st.subheader("⚙️ Configurazione Prima Settimana")
    excluded_first_week, priority_first_week = render_first_week_section(people)
    
    return {
        'people': people,
        'month': selected_month,
        'year': selected_year,
        'absences': absences,
        'excluded_first_week': excluded_first_week,
        'priority_first_week': priority_first_week
    }


def render_absences_section(people: List[str], year: int, month: int) -> Dict:
    """Renderizza la sezione gestione assenze."""
    
    # Inizializza il dizionario delle assenze
    if 'absences' not in st.session_state:
        st.session_state.absences = {}
    
    if not people:
        st.info("⚠️ Aggiungi prima delle persone per gestire le assenze")
        return {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Aggiungi Nuova Assenza:**")
        
        selected_person = st.selectbox("Seleziona persona:", people, key="absence_person")
        
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            start_date = st.date_input(
                "Data inizio:",
                datetime(year, month, 1),
                key="absence_start"
            )
        with subcol2:
            end_date = st.date_input(
                "Data fine:",
                datetime(year, month, 1),
                key="absence_end"
            )
        
        if st.button("➕ Aggiungi Assenza", type="secondary"):
            if selected_person not in st.session_state.absences:
                st.session_state.absences[selected_person] = []
            
            st.session_state.absences[selected_person].append((
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.min.time())
            ))
            st.success(f"✅ Assenza aggiunta per {selected_person}")
            st.rerun()
    
    with col2:
        st.markdown("**Assenze Registrate:**")
        if st.session_state.absences:
            for person, absence_list in st.session_state.absences.items():
                if absence_list:
                    st.write(f"**{person}:**")
                    for i, (start, end) in enumerate(absence_list):
                        subcol1, subcol2 = st.columns([4, 1])
                        with subcol1:
                            st.write(f"• {start.strftime('%d/%m')} - {end.strftime('%d/%m')}")
                        with subcol2:
                            if st.button("🗑️", key=f"del_absence_{person}_{i}"):
                                st.session_state.absences[person].pop(i)
                                st.rerun()
        else:
            st.info("Nessuna assenza registrata")
        
        if st.button("🔄 Cancella Tutte", key="clear_all_absences"):
            st.session_state.absences = {}
            st.success("Tutte le assenze cancellate!")
            st.rerun()
    
    return st.session_state.absences


def render_first_week_section(people: List[str]) -> Tuple[Dict, List[str]]:
    """Renderizza la sezione configurazione prima settimana."""
    
    rooms = st.session_state.scheduler.rooms
    
    # Inizializza configurazioni
    if 'excluded_first_week' not in st.session_state:
        st.session_state.excluded_first_week = {}
    if 'priority_first_week' not in st.session_state:
        st.session_state.priority_first_week = rooms.copy()
    
    if not people:
        st.info("⚠️ Aggiungi prima delle persone per configurare la prima settimana")
        return {}, rooms.copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🚫 Esclusioni Prima Settimana:**")
        selected_person_exclusion = st.selectbox(
            "Persona:",
            people,
            key="exclusion_person_main"
        )
        
        excluded_rooms = st.multiselect(
            "Stanze da NON assegnare:",
            rooms,
            default=st.session_state.excluded_first_week.get(selected_person_exclusion, []),
            key="excluded_rooms_main"
        )
        
        if st.button("💾 Salva Esclusioni", key="save_exclusions_main"):
            st.session_state.excluded_first_week[selected_person_exclusion] = excluded_rooms
            st.success(f"✅ Esclusioni salvate per {selected_person_exclusion}")
            st.rerun()
    
    with col2:
        st.markdown("**🎯 Priorità Stanze Prima Settimana:**")
        priority_rooms = st.multiselect(
            "Ordina le stanze per priorità:",
            rooms,
            default=st.session_state.priority_first_week,
            key="priority_rooms_main",
            help="L'ordine determina la priorità di assegnazione"
        )
        
        if st.button("💾 Salva Priorità", key="save_priorities_main"):
            st.session_state.priority_first_week = priority_rooms if priority_rooms else rooms.copy()
            st.success("✅ Priorità salvate!")
            st.rerun()
    
    # Mostra configurazioni correnti
    if st.session_state.excluded_first_week or st.session_state.priority_first_week != rooms:
        st.markdown("**📋 Configurazione Attuale Prima Settimana:**")
        
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            if st.session_state.excluded_first_week:
                st.write("**Esclusioni:**")
                for person, excluded in st.session_state.excluded_first_week.items():
                    if excluded:
                        st.write(f"• **{person}**: {', '.join(excluded)}")
        
        with subcol2:
            st.write(f"**Priorità**: {', '.join(st.session_state.priority_first_week)}")
        
        if st.button("🔄 Reset Configurazione Prima Settimana", key="reset_first_week"):
            st.session_state.excluded_first_week = {}
            st.session_state.priority_first_week = rooms.copy()
            st.success("✅ Configurazione resettata!")
            st.rerun()
    
    return (st.session_state.excluded_first_week, st.session_state.priority_first_week)


# Applicazione CSS
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Mostra la pagina
show_configuration_page()