"""
Scheduler principale per la gestione intelligente dei turni di pulizia.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
import calendar

from ..utils.constants import ALGORITMO_CONFIG
from ..utils.helpers import (
    get_month_weeks,
    is_person_available,
    format_date_italian
)


class CleaningScheduler:
    """Classe principale per la generazione intelligente dei turni di pulizia."""
    
    def __init__(self, rooms: Optional[List[str]] = None):
        """
        Inizializza lo scheduler.
        
        Args:
            rooms: Lista delle stanze da gestire
        """
        self.rooms = rooms or ["Bagno", "Cucina", "Veranda", "Corridoio"]
        self.italian_weekdays = {
            0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì",
            4: "Venerdì", 5: "Sabato", 6: "Domenica"
        }
    
    def generate_schedule(self, people: List[str], year: int, month: int, 
                         absences: Dict[str, List[Tuple[datetime, datetime]]],
                         excluded_first_week: Optional[Dict[str, List[str]]] = None,
                         priority_first_week: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Genera il calendario dei turni con giorni specifici.
        
        Args:
            people: Lista delle persone
            year: Anno di riferimento
            month: Mese di riferimento
            absences: Dizionario con le assenze per persona
            excluded_first_week: Stanze escluse per persona nella prima settimana
            priority_first_week: Priorità stanze per la prima settimana
            
        Returns:
            DataFrame con il piano completo
        """
        weeks = get_month_weeks(year, month)
        schedule_data = []
        
        # Inizializza i parametri opzionali
        if excluded_first_week is None:
            excluded_first_week = {}
        if priority_first_week is None:
            priority_first_week = self.rooms.copy()
        
        # Traccia chi ha fatto cosa la settimana precedente
        last_week_assignments = {}
        
        # Traccia stanze non assegnate la settimana precedente (per dare priorità)
        unassigned_last_week = set()
        
        # Traccia assegnazioni mensili per rotazione (evita ripetizioni stanza/persona nel mese)
        monthly_assignments = {person: set() for person in people}
        
        for week_num, (week_start, week_end) in enumerate(weeks, 1):
            # Analizza disponibilità per ogni persona in ogni giorno della settimana
            person_available_days = {}
            for person in people:
                person_available_days[person] = []
                for day_offset in range(7):
                    check_date = week_start + timedelta(days=day_offset)
                    if is_person_available(person, check_date, absences):
                        weekday_name = self.italian_weekdays[check_date.weekday()]
                        person_available_days[person].append((day_offset, check_date, weekday_name))
            
            # Algoritmo di distribuzione intelligente della settimana
            week_assignments = {}
            room_day_assignments = {}
            
            # Priorità giorni: evita weekend quando possibile
            day_priorities = [0, 1, 2, 3, 4, 5, 6]  # Lun-Ven preferiti, poi weekend
            
            # Ordine stanze per questa settimana con priorità per stanze non assegnate
            if week_num == 1:
                room_order = priority_first_week
            else:
                # Priorità a stanze non assegnate la settimana precedente
                priority_rooms = list(unassigned_last_week)
                remaining_rooms = [room for room in self.rooms if room not in unassigned_last_week]
                room_order = priority_rooms + remaining_rooms
            
            # Trova la migliore distribuzione settimanale
            best_weekly_assignment = self._find_optimal_weekly_distribution(
                people, person_available_days, room_order, week_num,
                excluded_first_week, last_week_assignments, day_priorities,
                self.italian_weekdays, week_start, monthly_assignments
            )
            
            # Applica l'assegnazione ottimale
            for room in room_order:
                if room in best_weekly_assignment:
                    person, (day_offset, date, weekday) = best_weekly_assignment[room]
                    week_assignments[room] = person
                    room_day_assignments[room] = (date, weekday)
                else:
                    # Nessuna assegnazione possibile per questa stanza
                    week_assignments[room] = "Nessuno disponibile"
                    fallback_date = week_start
                    fallback_weekday = self.italian_weekdays[fallback_date.weekday()]
                    room_day_assignments[room] = (fallback_date, fallback_weekday)
            
            # Aggiorna tracciamento per la settimana successiva
            last_week_assignments = week_assignments.copy()
            
            # Traccia stanze non assegnate per priorità settimana successiva
            unassigned_last_week = {room for room, person in week_assignments.items()
                                  if person == "Nessuno disponibile"}
            
            # Aggiorna il tracciamento delle assegnazioni mensili
            for room, person in week_assignments.items():
                if person not in ["Nessuno disponibile", "Non assegnato"]:
                    monthly_assignments[person].add(room)
            
            # Aggiungi al dataframe con giorni specifici
            for room in self.rooms:
                assigned_date, assigned_weekday = room_day_assignments.get(room, (week_start, "Lunedì"))
                schedule_data.append({
                    'Settimana': f"Settimana {week_num}",
                    'Periodo': f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}",
                    'Stanza': room,
                    'Persona': week_assignments.get(room, "Non assegnato"),
                    'Data_Specifica': assigned_date,
                    'Giorno_Settimana': assigned_weekday,
                    'Data_Completa': f"{assigned_weekday} {assigned_date.strftime('%d/%m')}",
                    'Data_Inizio': week_start,
                    'Data_Fine': week_end
                })
        
        df = pd.DataFrame(schedule_data)
        # Ordina per data specifica per visualizzazione cronologica
        df = df.sort_values(['Data_Specifica', 'Stanza'], ascending=[True, True])
        return df
    
    def _find_optimal_weekly_distribution(self, people, person_available_days, room_order, week_num,
                                        excluded_first_week, last_week_assignments, day_priorities,
                                        italian_weekdays, week_start, monthly_assignments):
        """Trova la distribuzione ottimale delle stanze nella settimana con approccio greedy intelligente."""
        
        # Crea lista di tutti i possibili slot (giorno, persona, stanza)
        all_possible_assignments = []
        
        for room in room_order:
            for person in people:
                # Controlli di validità base
                if not person_available_days[person]:
                    continue
                
                # Esclusioni prima settimana
                if week_num == 1 and person in excluded_first_week and room in excluded_first_week[person]:
                    continue
                
                # Evita ripetizioni settimane consecutive
                if room in last_week_assignments and last_week_assignments[room] == person:
                    continue
                
                # Logica rotazione mensile: evita che una persona rifaccia la stessa stanza
                # a meno che tutti gli altri DISPONIBILI l'abbiano già fatta
                if room in monthly_assignments[person]:
                    # Considera solo le persone effettivamente disponibili (non assenti)
                    available_people = [p for p in people if p != person and person_available_days[p]]
                    
                    # Se non ci sono altre persone disponibili, permetti la ripetizione
                    if not available_people:
                        pass  # Continua con l'assegnazione
                    else:
                        # Controlla se tutte le altre persone disponibili hanno già fatto questa stanza
                        all_available_others_done = all(room in monthly_assignments[other] 
                                                      for other in available_people)
                        if not all_available_others_done:
                            continue  # Skip per favorire rotazione
                
                # Aggiungi ogni giorno disponibile per questa persona
                for day_offset, date, weekday in person_available_days[person]:
                    # Calcola punteggio per questa assegnazione
                    score = self._calculate_assignment_score(person, day_offset, room, 
                                                           person_available_days, day_priorities)
                    all_possible_assignments.append((score, room, person, day_offset, date, weekday))
        
        # Ordina per punteggio decrescente
        all_possible_assignments.sort(reverse=True, key=lambda x: x[0])
        
        # Algoritmo bilanciato: distribuzione equa tra persone e giorni
        final_assignment = {}
        person_assignments_count = {person: 0 for person in people}
        used_days = set()
        
        # Prima fase: distribuzione primaria (una assegnazione per persona disponibile)
        available_people = [p for p in people if person_available_days[p]]
        target_per_person = max(1, len(room_order) // len(available_people)) if available_people else 1
        
        for score, room, person, day_offset, date, weekday in all_possible_assignments:
            # Controlli conflitti base
            if room in final_assignment:
                continue  # Stanza già assegnata
            if day_offset in used_days:
                continue  # Giorno già occupato
            
            # Priorità a persone con meno assegnazioni (bilanciamento)
            if person_assignments_count[person] < target_per_person:
                final_assignment[room] = (person, (day_offset, date, weekday))
                person_assignments_count[person] += 1
                used_days.add(day_offset)
        
        # Seconda fase: assegna stanze rimanenti con strategia di distribuzione giorni
        unassigned_rooms = [room for room in room_order if room not in final_assignment]
        if unassigned_rooms:
            # Traccia giorni usati per persona per favorire distribuzione
            person_used_days = {}
            for room, (person, (day_offset, date, weekday)) in final_assignment.items():
                if person not in person_used_days:
                    person_used_days[person] = set()
                person_used_days[person].add(day_offset)
            
            for room in unassigned_rooms[:]:
                best_assignment = None
                best_score = -1
                
                # Trova la migliore assegnazione bilanciando carico E distribuzione giorni
                for score, r, person, day_offset, date, weekday in all_possible_assignments:
                    if r != room:
                        continue
                    if room in final_assignment:
                        continue
                    
                    # Calcola punteggio complessivo per questa assegnazione
                    assignment_score = 0
                    
                    # Fattore 1: Preferisci persone con meno assegnazioni totali (50%)
                    max_assignments = max(person_assignments_count.values()) if person_assignments_count.values() else 1
                    load_factor = ALGORITMO_CONFIG['PESO_BILANCIAMENTO'] * 100 * (max_assignments - person_assignments_count[person]) / max(max_assignments, 1)
                    assignment_score += load_factor
                    
                    # Fattore 2: Preferisci giorni non ancora usati da questa persona (30%)
                    if person not in person_used_days:
                        person_used_days[person] = set()
                    if day_offset not in person_used_days[person]:
                        assignment_score += ALGORITMO_CONFIG['PESO_DISTRIBUZIONE_GIORNI'] * 100  # Bonus per nuovo giorno
                    else:
                        assignment_score += 5   # Penalità per giorno già usato
                    
                    # Fattore 3: Punteggio base dell'assegnazione (20%)
                    assignment_score += score * ALGORITMO_CONFIG['PESO_QUALITA_ASSEGNAZIONE']
                    
                    # Seleziona la migliore opzione
                    if assignment_score > best_score:
                        best_score = assignment_score
                        best_assignment = (person, day_offset, date, weekday)
                
                # Assegna la migliore opzione trovata
                if best_assignment:
                    person, day_offset, date, weekday = best_assignment
                    final_assignment[room] = (person, (day_offset, date, weekday))
                    person_assignments_count[person] += 1
                    if person not in person_used_days:
                        person_used_days[person] = set()
                    person_used_days[person].add(day_offset)
                    unassigned_rooms.remove(room)
        
        return final_assignment
    
    def _calculate_assignment_score(self, person, day_offset, room, person_available_days, day_priorities):
        """Calcola il punteggio per una singola assegnazione."""
        score = 0
        
        # Fattore 1: Preferisci persone più vincolate (meno giorni disponibili)
        total_days = len(person_available_days[person])
        if total_days <= 2:
            score += 100  # Persona molto vincolata: massima priorità
        elif total_days <= 4:
            score += 50   # Persona moderatamente vincolata
        else:
            score += 10   # Persona con molti giorni disponibili
        
        # Fattore 2: Preferisci giorni infrasettimanali se configurato
        if ALGORITMO_CONFIG['EVITA_WEEKEND']:
            if day_offset < 5:  # Lunedì-Venerdì
                score += 30
            else:  # Sabato-Domenica
                score += 5
        
        # Fattore 3: Distribuzione uniforme nella settimana
        # Preferisci giorni centrali (Mar-Gio) per distribuzione ottimale
        day_distribution_bonus = {
            0: 20,  # Lunedì: buono per inizio settimana
            1: 25,  # Martedì: ottimo
            2: 30,  # Mercoledì: perfetto (centro settimana)
            3: 25,  # Giovedì: ottimo
            4: 20,  # Venerdì: buono per fine settimana
            5: 10,  # Sabato: evita se possibile
            6: 5    # Domenica: ultimo resort
        }
        score += day_distribution_bonus.get(day_offset, 0)
        
        # Fattore 4: Randomizzazione per evitare sempre le stesse scelte
        score += random.randint(1, 10)
        
        return score