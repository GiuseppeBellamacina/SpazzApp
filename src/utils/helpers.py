"""
Funzioni di utilità per SpazzApp.
"""

from datetime import datetime, timedelta
import calendar
from typing import List, Dict, Tuple, Optional
import pandas as pd

from .constants import GIORNI_SETTIMANA, MESI_ITALIANI


def get_current_month_year() -> Tuple[int, int]:
    """Restituisce il mese e anno correnti."""
    now = datetime.now()
    return now.month, now.year


def get_month_name_italian(month: int) -> str:
    """Restituisce il nome del mese in italiano."""
    return MESI_ITALIANI[month - 1]


def get_weekday_italian(weekday: int) -> str:
    """Restituisce il nome del giorno della settimana in italiano."""
    return GIORNI_SETTIMANA[weekday]


def get_month_weeks(year: int, month: int) -> List[Tuple[datetime, datetime]]:
    """
    Restituisce le settimane del mese specificato.
    
    Args:
        year: Anno
        month: Mese (1-12)
        
    Returns:
        Lista di tuple (inizio_settimana, fine_settimana)
    """
    # Primo giorno del mese
    first_day = datetime(year, month, 1)
    # Ultimo giorno del mese
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    # Trova il lunedì della settimana contenente il primo giorno
    week_start = first_day - timedelta(days=first_day.weekday())
    
    weeks = []
    current_week_start = week_start
    
    while current_week_start <= last_day:
        week_end = current_week_start + timedelta(days=6)
        weeks.append((current_week_start, week_end))
        current_week_start += timedelta(days=7)
    
    return weeks


def is_person_available(person: str, date: datetime, absences: Dict[str, List[Tuple[datetime, datetime]]]) -> bool:
    """
    Verifica se una persona è disponibile in una data specifica.
    
    Args:
        person: Nome della persona
        date: Data da verificare
        absences: Dizionario con le assenze per persona (tuple di date di inizio e fine)
        
    Returns:
        True se la persona è disponibile
    """
    if person not in absences:
        return True
    
    for start_date, end_date in absences[person]:
        if start_date <= date <= end_date:
            return False
    return True


def format_date_italian(date: datetime) -> str:
    """Formatta una data in formato italiano."""
    italian_weekdays = {
        0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì",
        4: "Venerdì", 5: "Sabato", 6: "Domenica"
    }
    
    weekday_name = italian_weekdays[date.weekday()]
    return f"{weekday_name} {date.day}/{date.month}"


def calculate_workload_balance(assignments: Dict, people: List[str]) -> float:
    """
    Calcola il bilanciamento del carico di lavoro.
    
    Args:
        assignments: Dizionario delle assegnazioni
        people: Lista delle persone
        
    Returns:
        Punteggio di bilanciamento (più alto = meglio bilanciato)
    """
    person_counts = {person: 0 for person in people}
    
    for assignment in assignments.values():
        if assignment and assignment in people:
            person_counts[assignment] += 1
    
    if not any(person_counts.values()):
        return 0
    
    counts = list(person_counts.values())
    avg = sum(counts) / len(counts)
    variance = sum((count - avg) ** 2 for count in counts) / len(counts)
    
    # Più bassa la varianza, meglio è il bilanciamento
    return 1 / (1 + variance)


def calculate_day_distribution_score(assignments: Dict, total_rooms: int) -> float:
    """
    Calcola il punteggio di distribuzione dei giorni.
    
    Args:
        assignments: Dizionario {(stanza, giorno): persona}
        total_rooms: Numero totale di stanze
        
    Returns:
        Punteggio di distribuzione (più alto = meglio distribuito)
    """
    if not assignments:
        return 0
    
    day_counts = {}
    for (room, day), person in assignments.items():
        if person:
            day_counts[day] = day_counts.get(day, 0) + 1
    
    if not day_counts:
        return 0
    
    # Calcola quanto è uniforme la distribuzione
    counts = list(day_counts.values())
    if len(counts) <= 1:
        return 1.0
    
    avg = sum(counts) / len(counts)
    variance = sum((count - avg) ** 2 for count in counts) / len(counts)
    
    return 1 / (1 + variance)


def create_dataframe_from_schedule(schedule_data: List[Dict]) -> pd.DataFrame:
    """
    Crea un DataFrame dalle informazioni del piano.
    
    Args:
        schedule_data: Lista di dizionari con i dati del piano
        
    Returns:
        DataFrame ordinato cronologicamente
    """
    if not schedule_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(schedule_data)
    
    # Converti la colonna data in datetime se non è già
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'])
        df = df.sort_values('data')
    
    return df


def validate_configuration(people: List[str], rooms: List[str], 
                         excluded_first_week: Optional[Dict[str, List[str]]] = None,
                         priority_first_week: Optional[List[str]] = None) -> List[str]:
    """
    Valida la configurazione del sistema.
    
    Args:
        people: Lista delle persone
        rooms: Lista delle stanze
        excluded_first_week: Esclusioni prima settimana
        priority_first_week: Priorità prima settimana
        
    Returns:
        Lista di errori di validazione
    """
    errors = []
    
    if not people:
        errors.append("Deve essere specificata almeno una persona")
    
    if not rooms:
        errors.append("Deve essere specificata almeno una stanza")
    
    if excluded_first_week:
        for person, excluded_rooms in excluded_first_week.items():
            if person not in people:
                errors.append(f"Persona nelle esclusioni non trovata: {person}")
            
            for room in excluded_rooms:
                if room not in rooms:
                    errors.append(f"Stanza nelle esclusioni non trovata: {room}")
    
    if priority_first_week:
        for room in priority_first_week:
            if room not in rooms:
                errors.append(f"Stanza nelle priorità non trovata: {room}")
    
    return errors