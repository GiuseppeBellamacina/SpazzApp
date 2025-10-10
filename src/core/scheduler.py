"""
Scheduler principale per la gestione intelligente dei turni di pulizia.
Utilizza oggetti strutturati per una distribuzione equa e rotazione ottimale.
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple, Optional
import pandas as pd

from ..utils.helpers import get_month_weeks
from ..utils.constants import STANZE_DEFAULT
from .models import Person, WeeklyAssignment, RoomAssignment, SchedulingState


class CleaningScheduler:
    """Classe principale per la generazione intelligente dei turni di pulizia."""
    
    def __init__(self, rooms: Optional[List[str]] = None):
        """Inizializza lo scheduler con le stanze disponibili."""
        self.rooms = rooms if rooms else STANZE_DEFAULT

        # Mappatura giorni della settimana in italiano
        self.italian_weekdays = {
            0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì",
            4: "Venerdì", 5: "Sabato", 6: "Domenica"
        }

    def generate_schedule(self, people: List[str], year: int, month: int, 
                         absences: Dict[str, List[Tuple[datetime, datetime]]],
                         excluded_first_week: Optional[Dict[str, List[str]]] = None,
                         priority_first_week: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Genera il calendario dei turni usando oggetti strutturati per distribuzione ottimale.
        """
        print(f"\n=== INIZIO GENERAZIONE SCHEDULE CON OGGETTI ===")
        print(f"Persone: {people}")
        print(f"Anno/Mese: {year}/{month}")
        print(f"Stanze: {self.rooms}")
        
        weeks = get_month_weeks(year, month)
        
        if excluded_first_week is None:
            excluded_first_week = {}
        if priority_first_week is None:
            priority_first_week = self.rooms.copy()
        
        # Crea oggetti Person per ogni persona
        person_objects = []
        for person_name in people:
            person_obj = Person(person_name)
            person_obj.initialize_rooms(self.rooms)
            
            # Converti assenze in lista di date
            person_absences = []
            if person_name in absences:
                for absence_start, absence_end in absences[person_name]:
                    current_date = absence_start.date()
                    end_date = absence_end.date()
                    while current_date <= end_date:
                        person_absences.append(current_date)
                        current_date += timedelta(days=1)
            person_obj.absences = person_absences
            
            person_objects.append(person_obj)
        
        # Inizializza lo state del scheduling
        scheduling_state = SchedulingState(person_objects, self.rooms)
        
        print(f"\n=== PERSONE INIZIALIZZATE ===")
        for person in person_objects:
            print(f"{person.name}: {len(person.absences)} giorni di assenza")
        
        # Processa settimana per settimana
        for week_num, (week_start, week_end) in enumerate(weeks, 1):
            print(f"\n--- SETTIMANA {week_num}: {week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')} ---")
            
            # Crea WeeklyAssignment per ogni persona
            for person in person_objects:
                weekly_assignment = WeeklyAssignment(
                    week_number=week_num,
                    week_start=week_start.date(),
                    week_end=week_end.date()
                )
                person.weekly_data[week_num] = weekly_assignment
            
            # Trova persone disponibili questa settimana
            available_people = []
            for person in person_objects:
                available_days = person.get_available_days_in_week(week_start.date(), week_end.date())
                if available_days:
                    available_people.append(person)
                    print(f"{person.name}: {len(available_days)} giorni disponibili - {[d.strftime('%a %d') for d in available_days[:3]]}{'...' if len(available_days) > 3 else ''}")
            
            if not available_people:
                print("Nessuna persona disponibile questa settimana")
                continue
            
            # Assegna stanze per questa settimana usando il nuovo algoritmo
            self._assign_week_with_objects(
                available_people, week_num, excluded_first_week, scheduling_state
            )
        
        # Converti il risultato in DataFrame
        schedule_data = []
        for assignment in scheduling_state.assignments:
            week_start = None
            week_end = None
            
            # Trova i limiti della settimana per questo assignment
            for w_num, (w_start, w_end) in enumerate(weeks, 1):
                if w_num == assignment.week_number:
                    week_start = w_start
                    week_end = w_end
                    break
            
            if week_start is None or week_end is None:
                continue
                
            weekday_name = self.italian_weekdays[assignment.assignment_date.weekday()]
            schedule_data.append({
                'Settimana': f"Settimana {assignment.week_number}",
                'Periodo': f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}",
                'Stanza': assignment.room,
                'Persona': assignment.person.name,
                'Data_Specifica': assignment.assignment_date,
                'Giorno_Settimana': weekday_name,
                'Data_Completa': f"{weekday_name} {assignment.assignment_date.strftime('%d/%m')}",
                'Data_Inizio': week_start,
                'Data_Fine': week_end
            })
        
        # Stampa riassunto finale
        scheduling_state.print_summary()
        
        df = pd.DataFrame(schedule_data)
        # Ordina per data specifica per visualizzazione cronologica
        df = df.sort_values(['Data_Specifica', 'Stanza'], ascending=[True, True])
        
        print(f"\n=== FINE GENERAZIONE - TOTALE ASSEGNAZIONI: {len(schedule_data)} ===")
        return df

    def _assign_week_with_objects(self, available_people: List[Person], week_number: int, 
                                 excluded_first_week: Dict[str, List[str]], 
                                 scheduling_state: SchedulingState):
        """
        Assegna le stanze per una settimana usando gli oggetti Person per distribuzione ottimale.
        """
        print(f"DEBUG: Assegno settimana {week_number} con {len(available_people)} persone")
        
        num_rooms = len(self.rooms)
        
        # Calcola target per questa settimana considerando il bilanciamento globale
        person_targets = self._calculate_balanced_targets(available_people, num_rooms)
        
        print(f"Target per persona: {[(p.name, target) for p, target in person_targets.items()]}")
        print(f"Situazione attuale: {[(p.name, p.total_assignments) for p in available_people]}")
        
        # Ottieni tutti i giorni disponibili della settimana ordinati cronologicamente
        all_available_dates = set()
        for person in available_people:
            weekly = person.get_weekly_assignment(week_number)
            if weekly:
                person_days = person.get_available_days_in_week(weekly.week_start, weekly.week_end)
                all_available_dates.update(person_days)
        
        chronological_dates = sorted(list(all_available_dates))
        print(f"Giorni disponibili: {[d.strftime('%a %d') for d in chronological_dates]}")
        
        # Contatori per vincoli
        person_assignments_count = {person: 0 for person in available_people}
        rooms_assigned = set()
        
        # Algoritmo principale: itera cronologicamente sui giorni
        for current_date in chronological_dates:
            print(f"\n  Assegnazioni per {current_date.strftime('%a %d/%m')}:")
            
            # Trova stanze ancora da assegnare
            unassigned_rooms = [room for room in self.rooms if room not in rooms_assigned]
            if not unassigned_rooms:
                print("    Tutte le stanze già assegnate")
                break
            
            # Trova persone disponibili oggi che non hanno già un'assegnazione oggi
            available_today = []
            for person in available_people:
                weekly = person.get_weekly_assignment(week_number)
                if (weekly and 
                    person.is_available_on_date(current_date) and 
                    not person.has_used_day_in_week(current_date, week_number) and
                    person_assignments_count[person] < person_targets[person]):
                    available_today.append(person)
            
            if not available_today:
                print("    Nessuna persona disponibile oggi")
                continue
            
            print(f"    Persone disponibili oggi: {[p.name for p in available_today]}")
            
            # Calcola quante assegnazioni fare oggi (distribuisci equamente sui giorni)
            remaining_rooms = len(unassigned_rooms)
            remaining_dates = len([d for d in chronological_dates if d >= current_date])
            max_assignments_today = min(3, max(1, remaining_rooms // max(1, remaining_dates)))
            
            assignments_made_today = 0
            
            # Ordina le stanze per priorità di rotazione
            prioritized_rooms = self._prioritize_rooms_for_rotation(unassigned_rooms, available_today)
            
            for room in prioritized_rooms:
                if assignments_made_today >= max_assignments_today:
                    break
                
                if room in rooms_assigned:
                    continue
                
                # Trova la persona migliore per questa stanza
                best_person = self._find_best_person_for_room(
                    room, available_today, week_number, excluded_first_week, current_date
                )
                
                if best_person:
                    # Crea e aggiungi l'assegnazione
                    assignment = RoomAssignment(
                        room=room,
                        person=best_person,
                        assignment_date=current_date,
                        week_number=week_number
                    )
                    
                    scheduling_state.add_assignment(assignment)
                    rooms_assigned.add(room)
                    person_assignments_count[best_person] += 1
                    assignments_made_today += 1
                    
                    print(f"    ASSEGNATO: {room} -> {best_person.name}")
                    
                    # Rimuovi persona se ha raggiunto target
                    if person_assignments_count[best_person] >= person_targets[best_person]:
                        if best_person in available_today:
                            available_today.remove(best_person)
                
                else:
                    print(f"    Nessun candidato per {room}")
        
        # Gestisci stanze rimaste non assegnate (fallback)
        unassigned_rooms = [room for room in self.rooms if room not in rooms_assigned]
        if unassigned_rooms:
            print(f"\n  FALLBACK per stanze non assegnate: {unassigned_rooms}")
            self._assign_remaining_rooms_fallback(
                unassigned_rooms, available_people, week_number, scheduling_state, chronological_dates
            )
        
        print(f"\nAssegnazioni completate per settimana {week_number}")

    def _calculate_balanced_targets(self, available_people: List[Person], num_rooms: int) -> Dict[Person, int]:
        """
        Calcola i target per settimana bilanciando il carico di lavoro totale accumulato.
        """
        if not available_people:
            return {}
        
        # Calcola il carico di lavoro attuale per persona
        total_assignments = [person.total_assignments for person in available_people]
        min_assignments = min(total_assignments) if total_assignments else 0
        max_assignments = max(total_assignments) if total_assignments else 0
        
        print(f"  Carico attuale - Min: {min_assignments}, Max: {max_assignments}")
        
        # Calcola target base equo per questa settimana
        base_per_person = num_rooms // len(available_people)
        extra_rooms = num_rooms % len(available_people)
        
        person_targets = {}
        
        # Strategia: dai più lavoro a chi ha fatto meno finora
        for i, person in enumerate(available_people):
            current_load = person.total_assignments
            
            # Target base
            base_target = base_per_person
            
            # Bonus per chi è sotto la media
            if max_assignments > min_assignments:  # C'è squilibrio
                load_difference = max_assignments - current_load
                
                # Chi ha il carico minore ottiene le stanze extra
                if current_load == min_assignments and extra_rooms > 0:
                    bonus_rooms = min(extra_rooms, load_difference + 1)
                    base_target += bonus_rooms
                    extra_rooms -= bonus_rooms
                elif current_load < max_assignments and extra_rooms > 0:
                    # Chi è sotto il massimo può comunque ottenere stanze extra
                    bonus_rooms = min(1, extra_rooms)
                    base_target += bonus_rooms
                    extra_rooms -= bonus_rooms
            else:
                # Tutti hanno lo stesso carico, distribuisci normalmente
                if i < extra_rooms:
                    base_target += 1
            
            person_targets[person] = max(0, base_target)
        
        # Debug
        for person in available_people:
            target = person_targets[person]
            current = person.total_assignments
            print(f"    {person.name}: carico {current} -> target settimana {target}")
        
        return person_targets

    def _prioritize_rooms_for_rotation(self, rooms: List[str], available_people: List[Person]) -> List[str]:
        """
        Ordina le stanze per priorità di rotazione - prima quelle con maggiore disparità.
        """
        room_priorities = []
        
        for room in rooms:
            # Calcola la distribuzione di questa stanza tra le persone disponibili
            room_counts = []
            for person in available_people:
                room_counts.append(person.get_room_count(room))
            
            if not room_counts:
                priority_score = 0
            else:
                # Calcola disparità: differenza tra max e min
                min_count = min(room_counts)
                max_count = max(room_counts)
                disparity = max_count - min_count
                
                # Più alta la disparità, più alta la priorità
                priority_score = disparity * 100
                
                # Bonus per stanze mai fatte da qualcuno
                never_done_count = room_counts.count(0)
                priority_score += never_done_count * 50
                
                # Bonus per stanze generalmente poco assegnate
                avg_count = sum(room_counts) / len(room_counts)
                if avg_count < 1.0:
                    priority_score += 25
            
            room_priorities.append((priority_score, room))
        
        # Ordina per priorità decrescente
        room_priorities.sort(reverse=True, key=lambda x: x[0])
        
        prioritized_rooms = [room for score, room in room_priorities]
        print(f"    Ordine stanze per rotazione: {prioritized_rooms}")
        
        return prioritized_rooms

    def _find_best_person_for_room(self, room: str, available_people: List[Person], 
                                  week_number: int, excluded_first_week: Dict[str, List[str]], 
                                  assignment_date: date) -> Optional[Person]:
        """
        Trova la persona migliore per una stanza specifica basandosi sulla rotazione.
        """
        candidates = []
        
        for person in available_people:
            # Controlla esclusioni prima settimana
            if (week_number == 1 and 
                person.name in excluded_first_week and 
                room in excluded_first_week[person.name]):
                continue
            
            # Calcola punteggio per questa persona-stanza
            score = self._calculate_person_room_score_with_context(person, room, assignment_date, available_people)
            candidates.append((score, person))
        
        if not candidates:
            return None
        
        # Ordina per punteggio decrescente e prendi il migliore
        candidates.sort(reverse=True, key=lambda x: x[0])
        best_score, best_person = candidates[0]
        
        print(f"      {room} candidati: {[(f'{p.name}:{s:.0f}') for s, p in candidates[:3]]}")
        
        return best_person

    def _calculate_person_room_score(self, person: Person, room: str, assignment_date: date) -> float:
        """
        Calcola il punteggio per assegnare una specifica stanza a una persona.
        """
        score = 0.0
        
        # 1. ROTAZIONE STANZA SPECIFICA (peso maggiore)
        room_count = person.get_room_count(room)
        
        # Forte bonus per chi non ha mai pulito questa stanza
        if room_count == 0:
            score += 300  # Aumentato per dare più priorità alla rotazione
        elif room_count == 1:
            score += 150
        elif room_count == 2:
            score += 75
        else:
            score -= (room_count - 2) * 50  # penalità più alta per ripetizioni
        
        # 2. BILANCIAMENTO CARICO TOTALE - PESO MOLTO ALTO
        total_assignments = person.total_assignments
        
        # Calcola il carico minimo tra tutte le persone (approssimazione)
        # Questo è critico per evitare che una persona prenda tutto il carico
        min_possible_load = 0  # In teoria dovremmo passare tutte le persone, ma per ora approssimiamo
        
        # Forte bonus per chi ha carico basso
        if total_assignments <= 2:
            score += 500  # Priorità massima per chi ha fatto poco
        elif total_assignments <= 4:
            score += 300
        elif total_assignments <= 6:
            score += 150
        elif total_assignments <= 8:
            score += 50
        else:
            score -= (total_assignments - 8) * 100  # Forte penalità per sovraccarico
        
        # 3. PRIORITÀ GIORNI FERIALI
        if assignment_date.weekday() < 5:  # lun-ven
            score += 30
        else:  # weekend
            score += 10
        
        # 4. DISTRIBUZIONE TEMPORALE
        day_bonuses = {0: 15, 1: 12, 2: 10, 3: 8, 4: 5, 5: 3, 6: 1}  # lun-dom
        score += day_bonuses.get(assignment_date.weekday(), 0)
        
        return score

    def _calculate_person_room_score_with_context(self, person: Person, room: str, assignment_date: date, 
                                                 all_available_people: List[Person]) -> float:
        """
        Calcola il punteggio per una persona-stanza considerando il contesto di tutte le persone disponibili.
        """
        score = 0.0
        
        # 1. ROTAZIONE STANZA SPECIFICA (peso alto)
        room_count = person.get_room_count(room)
        
        # Calcola il minimo e massimo per questa stanza tra tutte le persone disponibili
        room_counts_all = [p.get_room_count(room) for p in all_available_people]
        min_room_count = min(room_counts_all)
        max_room_count = max(room_counts_all)
        
        # Forte priorità per chi ha il minimo per questa stanza
        if room_count == min_room_count:
            score += 400  # Priorità massima
        elif room_count == min_room_count + 1:
            score += 200
        else:
            # Penalità crescente per chi ha fatto di più
            score -= (room_count - min_room_count) * 100
        
        # 2. BILANCIAMENTO CARICO TOTALE - PESO CRITICO
        total_assignments = person.total_assignments
        
        # Calcola min/max carico tra persone disponibili
        total_loads = [p.total_assignments for p in all_available_people]
        min_load = min(total_loads)
        max_load = max(total_loads)
        
        # Priorità assoluta per chi ha il carico minimo
        if total_assignments == min_load:
            score += 600  # Priorità massima per bilanciamento
        elif total_assignments == min_load + 1:
            score += 400
        elif total_assignments == min_load + 2:
            score += 200
        else:
            # Forte penalità per chi è sopra il minimo
            load_excess = total_assignments - min_load
            score -= load_excess * 150
        
        # 3. PRIORITÀ GIORNI FERIALI
        if assignment_date.weekday() < 5:  # lun-ven
            score += 30
        else:  # weekend
            score += 10
        
        # 4. DISTRIBUZIONE TEMPORALE
        day_bonuses = {0: 15, 1: 12, 2: 10, 3: 8, 4: 5, 5: 3, 6: 1}
        score += day_bonuses.get(assignment_date.weekday(), 0)
        
        return score

    def _assign_remaining_rooms_fallback(self, remaining_rooms: List[str], 
                                       available_people: List[Person], 
                                       week_number: int, 
                                       scheduling_state: SchedulingState,
                                       available_dates: List[date]):
        """
        Assegna le stanze rimanenti con algoritmo fallback.
        """
        for room in remaining_rooms:
            best_assignment = None
            best_score = -1
            
            # Prova ogni combinazione persona-data
            for person in available_people:
                for assignment_date in available_dates:
                    if (person.is_available_on_date(assignment_date) and 
                        not person.has_used_day_in_week(assignment_date, week_number)):
                        
                        score = self._calculate_person_room_score_with_context(person, room, assignment_date, available_people)
                        if score > best_score:
                            best_score = score
                            best_assignment = (person, assignment_date)
            
            # Crea assegnazione fallback
            if best_assignment:
                person, assignment_date = best_assignment
                assignment = RoomAssignment(
                    room=room,
                    person=person,
                    assignment_date=assignment_date,
                    week_number=week_number
                )
                scheduling_state.add_assignment(assignment)
                print(f"  FALLBACK: {room} -> {person.name} il {assignment_date.strftime('%a %d')}")