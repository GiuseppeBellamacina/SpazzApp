"""
Componenti dell'interfaccia utente Streamlit.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Tuple

from ..utils.constants import MESI_ITALIANI, PERSONE_DEFAULT


class SidebarManager:
    """Gestisce la configurazione nella sidebar."""
    
    def __init__(self):
        """Inizializza il gestore della sidebar."""
        self.italian_months = {i: month for i, month in enumerate(MESI_ITALIANI, 1)}
    
    def render_sidebar_configuration(self, scheduler_rooms: List[str]) -> Dict:
        """
        Renderizza la configurazione nella sidebar.
        
        Args:
            scheduler_rooms: Lista delle stanze gestite dallo scheduler
            
        Returns:
            Dizionario con la configurazione
        """
        st.sidebar.header("⚙️ Configurazione")
        
        # Input persone
        people = self._render_people_input()
        
        # Selezione mese e anno
        month, year = self._render_month_year_selection()
        
        # Gestione assenze
        absences = self._render_absences_management(people, year, month)
        
        # Configurazione prima settimana
        excluded_first_week, priority_first_week = self._render_first_week_config(
            people, scheduler_rooms
        )
        
        # Informazioni sull'app
        self._render_app_info()
        
        return {
            'people': people,
            'month': month,
            'year': year,
            'absences': absences,
            'excluded_first_week': excluded_first_week,
            'priority_first_week': priority_first_week
        }
    
    def _render_people_input(self) -> List[str]:
        """Renderizza l'input per le persone."""
        st.sidebar.subheader("👥 Coinquilini")
        people_input = st.sidebar.text_area(
            "Inserisci i nomi (uno per riga):",
            value="\n".join(PERSONE_DEFAULT),
            help="Inserisci un nome per ogni riga"
        )
        return [name.strip() for name in people_input.split('\n') if name.strip()]
    
    def _render_month_year_selection(self) -> Tuple[int, int]:
        """Renderizza la selezione di mese e anno."""
        st.sidebar.subheader("📅 Periodo")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            selected_month = st.selectbox(
                "Mese:",
                range(1, 13),
                index=datetime.now().month - 1,
                format_func=lambda x: self.italian_months[x]
            )
        
        with col2:
            selected_year = st.selectbox(
                "Anno:",
                range(datetime.now().year, datetime.now().year + 2),
                index=0
            )
        
        return selected_month, selected_year
    
    def _render_absences_management(self, people: List[str], year: int, month: int) -> Dict:
        """Renderizza la gestione delle assenze."""
        st.sidebar.subheader("🚫 Gestione Assenze")
        
        # Inizializza il dizionario delle assenze nella sessione
        if 'absences' not in st.session_state:
            st.session_state.absences = {}
        
        if people:
            # Selezione persona per aggiungere assenza
            selected_person = st.sidebar.selectbox("Seleziona persona:", people)
            
            # Date di assenza
            col1, col2 = st.sidebar.columns(2)
            with col1:
                start_date = st.sidebar.date_input(
                    "Data inizio assenza:",
                    datetime(year, month, 1)
                )
            with col2:
                end_date = st.sidebar.date_input(
                    "Data fine assenza:",
                    datetime(year, month, 1)
                )
            
            if st.sidebar.button("➕ Aggiungi Assenza"):
                if selected_person not in st.session_state.absences:
                    st.session_state.absences[selected_person] = []
                
                st.session_state.absences[selected_person].append((
                    datetime.combine(start_date, datetime.min.time()),
                    datetime.combine(end_date, datetime.min.time())
                ))
                st.sidebar.success(f"Assenza aggiunta per {selected_person}")
            
            # Mostra assenze correnti
            self._show_current_absences()
        
        return st.session_state.absences
    
    def _show_current_absences(self):
        """Mostra le assenze correnti."""
        if st.session_state.absences:
            st.sidebar.subheader("📋 Assenze Registrate")
            for person, absence_list in st.session_state.absences.items():
                if absence_list:
                    st.sidebar.write(f"**{person}:**")
                    for i, (start, end) in enumerate(absence_list):
                        col1, col2 = st.sidebar.columns([3, 1])
                        with col1:
                            st.sidebar.write(f"• {start.strftime('%d/%m')} - {end.strftime('%d/%m')}")
                        with col2:
                            if st.sidebar.button("🗑️", key=f"del_{person}_{i}"):
                                st.session_state.absences[person].pop(i)
                                st.rerun()
        
        # Pulsante per cancellare tutte le assenze
        if st.sidebar.button("🔄 Cancella Tutte le Assenze"):
            st.session_state.absences = {}
            st.sidebar.success("Tutte le assenze sono state cancellate")
    
    def _render_first_week_config(self, people: List[str], rooms: List[str]) -> Tuple[Dict, List[str]]:
        """Renderizza la configurazione per la prima settimana."""
        st.sidebar.subheader("⚙️ Prima Settimana")
        
        # Inizializza le configurazioni nella sessione
        if 'excluded_first_week' not in st.session_state:
            st.session_state.excluded_first_week = {}
        if 'priority_first_week' not in st.session_state:
            st.session_state.priority_first_week = rooms.copy()
        
        if people:
            # Esclusioni per la prima settimana
            excluded_first_week = self._render_exclusions(people, rooms)
            
            # Priorità stanze prima settimana
            priority_first_week = self._render_priorities(rooms)
            
            # Reset configurazione prima settimana
            if st.sidebar.button("🔄 Reset Prima Settimana"):
                st.session_state.excluded_first_week = {}
                st.session_state.priority_first_week = rooms.copy()
                st.sidebar.success("Configurazione prima settimana resettata!")
        
        return (st.session_state.get('excluded_first_week', {}),
                st.session_state.get('priority_first_week', rooms.copy()))
    
    def _render_exclusions(self, people: List[str], rooms: List[str]) -> Dict[str, List[str]]:
        """Renderizza le esclusioni per la prima settimana."""
        st.sidebar.markdown("**🚫 Stanze da escludere (prima settimana):**")
        selected_person_exclusion = st.sidebar.selectbox(
            "Persona per esclusione:",
            people,
            key="exclusion_person"
        )
        
        excluded_rooms = st.sidebar.multiselect(
            "Stanze da NON assegnare:",
            rooms,
            default=st.session_state.excluded_first_week.get(selected_person_exclusion, []),
            key="excluded_rooms"
        )
        
        if st.sidebar.button("💾 Salva Esclusioni"):
            st.session_state.excluded_first_week[selected_person_exclusion] = excluded_rooms
            st.sidebar.success(f"Esclusioni salvate per {selected_person_exclusion}")
        
        # Mostra esclusioni correnti
        if st.session_state.excluded_first_week:
            st.sidebar.markdown("**📋 Esclusioni Registrate:**")
            for person, rooms_excluded in st.session_state.excluded_first_week.items():
                if rooms_excluded:
                    st.sidebar.write(f"• **{person}**: {', '.join(rooms_excluded)}")
        
        return st.session_state.excluded_first_week
    
    def _render_priorities(self, rooms: List[str]) -> List[str]:
        """Renderizza le priorità per la prima settimana."""
        st.sidebar.markdown("**🎯 Ordine priorità stanze (prima settimana):**")
        priority_rooms = st.sidebar.multiselect(
            "Riordina le stanze per priorità:",
            rooms,
            default=st.session_state.priority_first_week,
            key="priority_rooms"
        )
        
        if st.sidebar.button("💾 Salva Priorità"):
            st.session_state.priority_first_week = priority_rooms if priority_rooms else rooms.copy()
            st.sidebar.success("Priorità salvate!")
        
        return st.session_state.priority_first_week
    
    def _render_app_info(self):
        """Renderizza le informazioni sull'app."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
        ### ℹ️ Come usare SpazzApp:
        1. **Inserisci i coinquilini** nella lista
        2. **Seleziona mese e anno** (già preselezionati)
        3. **Configura esclusioni** prima settimana
        4. **Imposta priorità** stanze  
        5. **Aggiungi eventuali assenze**
        6. **Genera i turni** intelligenti
        7. **Scarica il piano** in PNG
        
        ### 📋 Stanze gestite:
        - 🚿 **Bagno**
        - 🍳 **Cucina**
        - 🌿 **Veranda**
        - 🚪 **Corridoio**
        
        ### 🎯 Algoritmo intelligente:
        - **Giorni flessibili** Lun-Dom
        - **Priorità persone vincolate** (pochi giorni disponibili)
        - **Evita sovrapposizioni** stesso giorno
        - **Rispetta configurazioni** esclusioni/priorità
        - **Gestione assenze** avanzata
        
        ### ✨ Vantaggi:
        - Massima flessibilità temporale
        - Ottimizzazione automatica
        - Adatto a orari complessi
        """)


class ScheduleDisplayManager:
    """Gestisce la visualizzazione del piano dei turni."""
    
    @staticmethod
    def display_schedule(schedule_df, scheduler_rooms: List[str], italian_months: Dict[int, str],
                        selected_month: int, selected_year: int):
        """
        Visualizza il piano dei turni in formato cronologico con card.
        
        Args:
            schedule_df: DataFrame con il piano
            scheduler_rooms: Lista delle stanze
            italian_months: Dizionario mesi italiani
            selected_month: Mese selezionato
            selected_year: Anno selezionato
        """
        # Mostra il calendario
        st.subheader(f"📅 Turni per {italian_months[selected_month]} {selected_year}")
        
        # Vista per settimane (ordinate cronologicamente)
        weeks_data = schedule_df.groupby('Settimana').first().sort_values('Data_Inizio')
        weeks = weeks_data.index.tolist()
        
        for week in weeks:
            week_data = schedule_df[schedule_df['Settimana'] == week]
            periodo = week_data.iloc[0]['Periodo']
            
            st.markdown(f"### {week} ({periodo})")
            
            # Ordina le assegnazioni per data specifica (cronologico) ma visualizza a blocchi
            week_data_sorted = week_data.sort_values('Data_Specifica')
            
            # Crea colonne per visualizzazione a blocchi (4 colonne per le 4 stanze)
            cols = st.columns(len(scheduler_rooms))
            
            # Riempi le colonne in ordine cronologico
            for i, (_, row) in enumerate(week_data_sorted.iterrows()):
                person = row['Persona']
                room = row['Stanza'] 
                day_info = row['Data_Completa']
                
                with cols[i % len(scheduler_rooms)]:
                    if person == "Nessuno disponibile":
                        st.markdown(f"""
                        <div class="room-card" style="border-left-color: #e74c3c;">
                            <h4>🚫 {room}</h4>
                            <p style="color: #e74c3c; font-weight: bold;">{person}</p>
                            <p style="color: #666; font-size: 0.9em;">📅 {day_info}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="room-card">
                            <h4>🏠 {room}</h4>
                            <p style="font-weight: bold; color: #2ecc71;">👤 {person}</p>
                            <p style="color: #1f77b4; font-weight: bold; font-size: 0.9em;">📅 {day_info}</p>
                        </div>
                        """, unsafe_allow_html=True)