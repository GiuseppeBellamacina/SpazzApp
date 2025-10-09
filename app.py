import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from typing import List, Dict, Tuple
import random

# Configurazione pagina
st.set_page_config(
    page_title="🏠 Gestione Turni Pulizie",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stili CSS personalizzati
st.markdown("""
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
""", unsafe_allow_html=True)

class CleaningScheduler:
    def __init__(self):
        self.rooms = ["Bagno", "Cucina", "Veranda", "Corridoio"]
        
    def get_month_weeks(self, year: int, month: int) -> List[Tuple[datetime, datetime]]:
        """Ottiene le settimane di un mese"""
        # Primo giorno del mese
        first_day = datetime(year, month, 1)
        # Ultimo giorno del mese
        last_day = datetime(year, month, calendar.monthrange(year, month)[1])
        
        # Trova il lunedì della prima settimana
        week_start = first_day - timedelta(days=first_day.weekday())
        
        weeks = []
        current = week_start
        
        while current <= last_day:
            week_end = current + timedelta(days=6)
            # Solo settimane che hanno almeno un giorno nel mese target
            if (current <= last_day and week_end >= first_day):
                weeks.append((current, week_end))
            current += timedelta(days=7)
            
        return weeks
    
    def is_person_available(self, person: str, date: datetime, absences: Dict[str, List[Tuple[datetime, datetime]]]) -> bool:
        """Controlla se una persona è disponibile in una data"""
        if person not in absences:
            return True
            
        for start_date, end_date in absences[person]:
            if start_date <= date <= end_date:
                return False
        return True
    
    def generate_schedule(self, people: List[str], year: int, month: int, 
                         absences: Dict[str, List[Tuple[datetime, datetime]]]) -> pd.DataFrame:
        """Genera il calendario dei turni"""
        weeks = self.get_month_weeks(year, month)
        schedule_data = []
        
        # Traccia chi ha fatto cosa la settimana precedente
        last_week_assignments = {}
        
        for week_num, (week_start, week_end) in enumerate(weeks, 1):
            # Crea una copia delle persone disponibili per questa settimana
            available_people = {}
            for room in self.rooms:
                available_people[room] = []
                for person in people:
                    # Controlla disponibilità per tutti i giorni della settimana
                    is_available = True
                    for day_offset in range(7):
                        check_date = week_start + timedelta(days=day_offset)
                        if not self.is_person_available(person, check_date, absences):
                            is_available = False
                            break
                    
                    if is_available:
                        available_people[room].append(person)
            
            # Assegna le stanze per questa settimana
            week_assignments = {}
            used_people = set()
            
            # Prima priorità: evitare di assegnare la stessa stanza alla stessa persona
            for room in self.rooms:
                available_for_room = [p for p in available_people[room] 
                                    if p not in used_people and 
                                    (room not in last_week_assignments or 
                                     last_week_assignments[room] != p)]
                
                if available_for_room:
                    assigned_person = random.choice(available_for_room)
                else:
                    # Se non ci sono persone disponibili che non hanno già fatto questa stanza,
                    # assegna a qualcuno di disponibile
                    available_for_room = [p for p in available_people[room] if p not in used_people]
                    if available_for_room:
                        assigned_person = random.choice(available_for_room)
                    else:
                        # Ultima risorsa: assegna a chiunque sia disponibile
                        if available_people[room]:
                            assigned_person = random.choice(available_people[room])
                        else:
                            assigned_person = "Nessuno disponibile"
                
                if assigned_person != "Nessuno disponibile":
                    week_assignments[room] = assigned_person
                    used_people.add(assigned_person)
                else:
                    week_assignments[room] = assigned_person
            
            # Salva le assegnazioni per la prossima settimana
            last_week_assignments = week_assignments.copy()
            
            # Aggiungi al dataframe
            for room in self.rooms:
                schedule_data.append({
                    'Settimana': f"Settimana {week_num}",
                    'Periodo': f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}",
                    'Stanza': room,
                    'Persona': week_assignments.get(room, "Non assegnato"),
                    'Data_Inizio': week_start,
                    'Data_Fine': week_end
                })
        
        return pd.DataFrame(schedule_data)

def main():
    # Header
    st.markdown('<div class="main-header">🏠 Gestione Turni Pulizie 🧹</div>', unsafe_allow_html=True)
    
    # Inizializza il generatore di turni
    scheduler = CleaningScheduler()
    
    # Sidebar per configurazione
    st.sidebar.header("⚙️ Configurazione")
    
    # Input persone
    st.sidebar.subheader("👥 Coinquilini")
    people_input = st.sidebar.text_area(
        "Inserisci i nomi (uno per riga):", 
        value="Alice\nBob\nCarlos\nDiana",
        help="Inserisci un nome per ogni riga"
    )
    people = [name.strip() for name in people_input.split('\n') if name.strip()]
    
    # Selezione mese e anno
    st.sidebar.subheader("📅 Periodo")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        selected_month = st.selectbox(
            "Mese:",
            range(1, 13),
            index=datetime.now().month - 1,
            format_func=lambda x: calendar.month_name[x]
        )
    
    with col2:
        selected_year = st.selectbox(
            "Anno:",
            range(datetime.now().year, datetime.now().year + 2),
            index=0
        )
    
    # Sezione assenze
    st.sidebar.subheader("🚫 Gestione Assenze")
    
    # Inizializza il dizionario delle assenze nella sessione
    if 'absences' not in st.session_state:
        st.session_state.absences = {}
    
    # Selezione persona per aggiungere assenza
    if people:
        selected_person = st.sidebar.selectbox("Seleziona persona:", people)
        
        # Date di assenza
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.sidebar.date_input(
                "Data inizio assenza:",
                datetime(selected_year, selected_month, 1)
            )
        with col2:
            end_date = st.sidebar.date_input(
                "Data fine assenza:",
                datetime(selected_year, selected_month, 1)
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
    
    # Area principale
    if len(people) < 2:
        st.warning("⚠️ Inserisci almeno 2 persone per generare i turni!")
        return
    
    # Genera turni
    if st.button("🎲 Genera Turni", type="primary", use_container_width=True):
        with st.spinner("Generando i turni..."):
            schedule_df = scheduler.generate_schedule(
                people, selected_year, selected_month, st.session_state.absences
            )
        
        st.success("✅ Turni generati con successo!")
        
        # Mostra il calendario
        st.subheader(f"📅 Turni per {calendar.month_name[selected_month]} {selected_year}")
        
        # Vista per settimane
        weeks = schedule_df['Settimana'].unique()
        
        for week in weeks:
            week_data = schedule_df[schedule_df['Settimana'] == week]
            periodo = week_data.iloc[0]['Periodo']
            
            st.markdown(f"### {week} ({periodo})")
            
            cols = st.columns(len(scheduler.rooms))
            
            for i, room in enumerate(scheduler.rooms):
                room_data = week_data[week_data['Stanza'] == room]
                if not room_data.empty:
                    person = room_data.iloc[0]['Persona']
                    with cols[i]:
                        if person == "Nessuno disponibile":
                            st.markdown(f"""
                            <div class="room-card" style="border-left-color: #e74c3c;">
                                <h4>🚫 {room}</h4>
                                <p style="color: #e74c3c; font-weight: bold;">{person}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="room-card">
                                <h4>🏠 {room}</h4>
                                <p style="font-weight: bold; color: #2ecc71;">👤 {person}</p>
                            </div>
                            """, unsafe_allow_html=True)
        
        # Tabella riassuntiva
        st.subheader("📊 Tabella Riassuntiva")
        
        # Raggruppa per persona
        summary_data = []
        for person in people:
            person_tasks = schedule_df[schedule_df['Persona'] == person]
            task_count = len(person_tasks)
            rooms_assigned = person_tasks['Stanza'].tolist()
            
            summary_data.append({
                'Persona': person,
                'Numero Turni': task_count,
                'Stanze Assegnate': ', '.join(rooms_assigned) if rooms_assigned else 'Nessuna'
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
        
        # Esporta CSV
        csv = schedule_df.to_csv(index=False)
        st.download_button(
            label="📥 Scarica Turni (CSV)",
            data=csv,
            file_name=f"turni_pulizie_{calendar.month_name[selected_month]}_{selected_year}.csv",
            mime="text/csv"
        )
    
    # Informazioni sull'app
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### ℹ️ Come usare l'app:
    1. **Inserisci i coinquilini** nella lista
    2. **Seleziona mese e anno**
    3. **Aggiungi eventuali assenze**
    4. **Genera i turni** con il pulsante
    5. **Scarica il calendario** in CSV
    
    ### 📋 Stanze gestite:
    - 🚿 Bagno
    - 🍳 Cucina  
    - 🌿 Veranda
    - 🚪 Corridoio
    """)

if __name__ == "__main__":
    main()