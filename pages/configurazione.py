"""
Pagina di configurazione per SpazzApp.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Tuple
from src.core.scheduler import CleaningScheduler
from src.utils.constants import CSS_STYLES, MESI_ITALIANI, PERSONE_DEFAULT, ACCORPAMENTO_DEFAULT


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
        
        # Mostra configurazione accorpamento
        st.markdown("**🔗 Accorpamento stanze:**")
        if config['room_groups_config'].get('abilitato', False):
            gruppi = config['room_groups_config'].get('gruppi', [])
            if gruppi:
                st.write(f"✅ Attivo con {len(gruppi)} gruppo/i configurati")
                for gruppo in gruppi:
                    st.write(f"• {gruppo['nome']}: {', '.join(gruppo['stanze'])}")
            else:
                st.write("⚠️ Attivo ma nessun gruppo configurato")
        else:
            st.write("❌ Disabilitato")
    
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
    
    st.markdown("---")
    
    # Sezione 5: Accorpamento Stanze per 3 Persone
    st.subheader("🔗 Accorpamento Stanze (3 Persone)")
    room_groups_config = render_room_grouping_section()
    
    return {
        'people': people,
        'month': selected_month,
        'year': selected_year,
        'absences': absences,
        'excluded_first_week': excluded_first_week,
        'priority_first_week': priority_first_week,
        'room_groups_config': room_groups_config
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


def render_room_grouping_section() -> Dict:
    """Renderizza la sezione per configurare l'accorpamento delle stanze."""
    
    # Inizializza configurazione accorpamento
    if 'room_groups_config' not in st.session_state:
        st.session_state.room_groups_config = ACCORPAMENTO_DEFAULT.copy()
    
    rooms = st.session_state.scheduler.rooms
    
    st.info("""
    💡 **Accorpamento Stanze**: Quando ci sono solo 3 persone disponibili in una settimana, 
    puoi configurare gruppi di stanze da assegnare insieme alla stessa persona.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎛️ Configurazione Generale:**")
        
        # Switch per abilitare/disabilitare
        accorpamento_abilitato = st.checkbox(
            "Abilita accorpamento per 3 persone",
            value=st.session_state.room_groups_config.get('abilitato', True),
            help="Quando attivo, con 3 persone disponibili le stanze configurate verranno accorpate"
        )
        
        st.session_state.room_groups_config['abilitato'] = accorpamento_abilitato
        
        if accorpamento_abilitato:
            st.success("✅ Accorpamento attivo")
            
            st.markdown("**➕ Aggiungi Nuovo Gruppo:**")
            
            # Form per aggiungere nuovo gruppo
            with st.form("nuovo_gruppo_form"):
                nome_gruppo = st.text_input(
                    "Nome del gruppo:",
                    placeholder="es: Cucina + Veranda"
                )
                
                stanze_gruppo = st.multiselect(
                    "Seleziona stanze da accorpare:",
                    rooms,
                    help="Seleziona almeno 2 stanze"
                )
                
                descrizione_gruppo = st.text_input(
                    "Descrizione (opzionale):",
                    placeholder="es: Zone cucina e veranda unificate"
                )
                
                submitted = st.form_submit_button("➕ Aggiungi Gruppo")
                
                if submitted:
                    if nome_gruppo and len(stanze_gruppo) >= 2:
                        # Aggiungi gruppo alla configurazione
                        if 'gruppi' not in st.session_state.room_groups_config:
                            st.session_state.room_groups_config['gruppi'] = []
                        
                        nuovo_gruppo = {
                            'nome': nome_gruppo,
                            'stanze': stanze_gruppo,
                            'descrizione': descrizione_gruppo
                        }
                        
                        st.session_state.room_groups_config['gruppi'].append(nuovo_gruppo)
                        st.success(f"✅ Gruppo '{nome_gruppo}' aggiunto!")
                        st.rerun()
                    else:
                        if not nome_gruppo:
                            st.error("❌ Inserisci un nome per il gruppo")
                        if len(stanze_gruppo) < 2:
                            st.error("❌ Seleziona almeno 2 stanze")
        else:
            st.warning("⚠️ Accorpamento disabilitato")
    
    with col2:
        st.markdown("**📋 Gruppi Configurati:**")
        
        gruppi_esistenti = st.session_state.room_groups_config.get('gruppi', [])
        
        if gruppi_esistenti:
            for i, gruppo in enumerate(gruppi_esistenti):
                with st.container():
                    st.markdown(f"**{gruppo['nome']}**")
                    st.write(f"🏠 Stanze: {', '.join(gruppo['stanze'])}")
                    if gruppo.get('descrizione'):
                        st.write(f"📝 {gruppo['descrizione']}")
                    
                    col_edit, col_delete = st.columns(2)
                    
                    with col_delete:
                        if st.button(f"🗑️ Elimina", key=f"delete_group_{i}"):
                            st.session_state.room_groups_config['gruppi'].pop(i)
                            st.success(f"Gruppo '{gruppo['nome']}' eliminato!")
                            st.rerun()
                    
                    st.markdown("---")
        else:
            if accorpamento_abilitato:
                st.info("Nessun gruppo configurato. Aggiungi un gruppo nella colonna a sinistra.")
            else:
                st.info("Accorpamento disabilitato.")
        
        # Pulsante reset
        if gruppi_esistenti and st.button("🔄 Reset Tutti i Gruppi"):
            st.session_state.room_groups_config['gruppi'] = []
            st.success("✅ Tutti i gruppi eliminati!")
            st.rerun()
    
    # Anteprima configurazione finale
    if accorpamento_abilitato and gruppi_esistenti:
        st.markdown("**🔍 Anteprima Configurazione:**")
        
        col_grouped, col_single = st.columns(2)
        
        with col_grouped:
            st.markdown("**Stanze Accorpate:**")
            stanze_accorpate = set()
            for gruppo in gruppi_esistenti:
                st.write(f"• **{gruppo['nome']}**: {', '.join(gruppo['stanze'])}")
                stanze_accorpate.update(gruppo['stanze'])
        
        with col_single:
            st.markdown("**Stanze Singole:**")
            stanze_singole = [room for room in rooms if room not in stanze_accorpate]
            if stanze_singole:
                for room in stanze_singole:
                    st.write(f"• {room}")
            else:
                st.write("Nessuna stanza singola")
        
        # Calcola unità totali
        unita_totali = len(gruppi_esistenti) + len(stanze_singole)
        
        if unita_totali == 3:
            st.success(f"✅ Configurazione ottimale: {unita_totali} unità per 3 persone")
        elif unita_totali < 3:
            st.warning(f"⚠️ Solo {unita_totali} unità configurate. Con 3 persone qualcuno avrà carico minore.")
        else:
            st.warning(f"⚠️ {unita_totali} unità configurate. Con 3 persone qualcuno avrà carico maggiore.")
    
    return st.session_state.room_groups_config


# Applicazione CSS
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Mostra la pagina
show_configuration_page()