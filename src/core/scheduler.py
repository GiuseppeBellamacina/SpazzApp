"""
Scheduler principale per la gestione intelligente dei turni di pulizia.
Utilizza oggetti strutturati per una distribuzione equa e rotazione ottimale.
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple, Optional
import pandas as pd

from ..utils.helpers import get_month_weeks
from ..utils.constants import STANZE_DEFAULT, ACCORPAMENTO_DEFAULT
from .models import Person, WeeklyAssignment, RoomAssignment, SchedulingState, RoomGroup


class CleaningScheduler:
    """Classe principale per la generazione intelligente dei turni di pulizia."""
    
    def __init__(self, rooms: Optional[List[str]] = None, room_groups_config: Optional[Dict] = None):
        """Inizializza lo scheduler con le stanze disponibili e configurazione accorpamento."""
        self.rooms = rooms if rooms else STANZE_DEFAULT
        self.room_groups_config = room_groups_config if room_groups_config else ACCORPAMENTO_DEFAULT
        
        # Crea oggetti RoomGroup dalla configurazione
        self.room_groups = []
        if self.room_groups_config and self.room_groups_config.get('abilitato', False):
            for group_config in self.room_groups_config.get('gruppi', []):
                # Verifica che tutte le stanze del gruppo esistano
                valid_rooms = [room for room in group_config['stanze'] if room in self.rooms]
                if len(valid_rooms) >= 2:  # Gruppo valido solo se ha almeno 2 stanze
                    self.room_groups.append(RoomGroup(
                        nome=group_config['nome'],
                        stanze=valid_rooms,
                        descrizione=group_config.get('descrizione', '')
                    ))

        # Mappatura giorni della settimana in italiano
        self.italian_weekdays = {
            0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì",
            4: "Venerdì", 5: "Sabato", 6: "Domenica"
        }

    def generate_schedule(self, people: List[str], year: int, month: int, 
                         absences: Dict[str, List[Tuple[datetime, datetime]]],
                         excluded_first_week: Optional[Dict[str, List[str]]] = None,
                         priority_first_week: Optional[List[str]] = None,
                         room_groups_config: Optional[Dict] = None) -> pd.DataFrame:
        """
        Genera il calendario dei turni usando oggetti strutturati per distribuzione ottimale.
        """
        # Aggiorna configurazione gruppi se fornita
        if room_groups_config is not None:
            self.room_groups_config = room_groups_config
            # Ricrea i gruppi
            self.room_groups = []
            if self.room_groups_config and self.room_groups_config.get('abilitato', False):
                for group_config in self.room_groups_config.get('gruppi', []):
                    valid_rooms = [room for room in group_config['stanze'] if room in self.rooms]
                    if len(valid_rooms) >= 2:
                        self.room_groups.append(RoomGroup(
                            nome=group_config['nome'],
                            stanze=valid_rooms,
                            descrizione=group_config.get('descrizione', '')
                        ))
        
        print(f"\n=== INIZIO GENERAZIONE SCHEDULE CON OGGETTI ===")
        print(f"Persone: {people}")
        print(f"Anno/Mese: {year}/{month}")
        print(f"Stanze: {self.rooms}")
        print(f"Gruppi stanze configurati: {len(self.room_groups)}")
        if self.room_groups:
            for group in self.room_groups:
                print(f"  - {group.nome}: {group.stanze}")
        
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
        
        # Controlla se attivare l'accorpamento per 3 persone
        should_group_rooms = (
            len(available_people) == 3 and 
            self.room_groups_config.get('abilitato', False) and 
            len(self.room_groups) > 0
        )
        
        if should_group_rooms:
            print(f"🔗 ACCORPAMENTO ATTIVATO: {len(available_people)} persone, gruppi disponibili: {[g.nome for g in self.room_groups]}")
            self._assign_week_with_grouping(available_people, week_number, excluded_first_week, scheduling_state)
            return
        
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
    
    def _assign_week_with_grouping(self, available_people: List[Person], week_number: int, 
                                  excluded_first_week: Dict[str, List[str]], 
                                  scheduling_state: SchedulingState):
        """
        Assegna le stanze per una settimana con accorpamento quando ci sono 3 persone.
        """
        print(f"🔗 Assegnazione con accorpamento per settimana {week_number}")
        
        # Ottieni tutti i giorni disponibili della settimana
        all_available_dates = set()
        for person in available_people:
            weekly = person.get_weekly_assignment(week_number)
            if weekly:
                person_days = person.get_available_days_in_week(weekly.week_start, weekly.week_end)
                all_available_dates.update(person_days)
        
        chronological_dates = sorted(list(all_available_dates))
        print(f"Giorni disponibili: {[d.strftime('%a %d') for d in chronological_dates]}")
        
        # Crea una lista delle "unità" da assegnare (singole stanze + gruppi)
        assignment_units = []
        grouped_rooms = set()
        
        # Aggiungi i gruppi come unità singole
        for group in self.room_groups:
            # Verifica che tutte le stanze del gruppo siano disponibili
            group_rooms_available = [room for room in group.stanze if room in self.rooms]
            if len(group_rooms_available) >= 2:
                assignment_units.append({
                    'type': 'group',
                    'rooms': group_rooms_available,
                    'name': group.nome,
                    'description': group.descrizione
                })
                grouped_rooms.update(group_rooms_available)
                print(f"  Gruppo: {group.nome} ({group_rooms_available})")
        
        # Aggiungi le stanze singole non accorpate
        for room in self.rooms:
            if room not in grouped_rooms:
                assignment_units.append({
                    'type': 'single',
                    'rooms': [room],
                    'name': room,
                    'description': f"Stanza singola: {room}"
                })
        
        print(f"Unità da assegnare: {len(assignment_units)} (gruppi: {len([u for u in assignment_units if u['type'] == 'group'])})")
        
        # Ora assegna le unità (3 persone, dovrebbero essere 3 unità)
        if len(assignment_units) != 3:
            print(f"⚠️  Numero unità ({len(assignment_units)}) != 3 persone. Fallback ad assegnazione normale.")
            # Fallback alla logica normale se non combacia
            self._assign_week_normal_logic(available_people, week_number, excluded_first_week, scheduling_state, chronological_dates)
            return
        
        # Calcola target bilanciati considerando che i gruppi contano come multipli
        unit_weights = {}
        for unit in assignment_units:
            unit_weights[unit['name']] = len(unit['rooms'])  # Peso = numero stanze nel gruppo/unità
        
        person_targets = self._calculate_balanced_targets_with_grouping(available_people, unit_weights)
        
        # Assegna le unità con algoritmo intelligente per bilanciamento
        assignments_made = self._assign_units_with_balancing(
            assignment_units, available_people, chronological_dates, 
            week_number, excluded_first_week, scheduling_state
        )
        
        print(f"Accorpamento completato: {len(assignments_made)} assegnazioni totali")
    
    def _assign_week_normal_logic(self, available_people: List[Person], week_number: int, 
                                 excluded_first_week: Dict[str, List[str]], 
                                 scheduling_state: SchedulingState,
                                 chronological_dates: List[date]):
        """
        Esegue la logica di assegnazione normale (senza accorpamento).
        """
        print("📋 Esecuzione logica normale (senza accorpamento)")
        
        num_rooms = len(self.rooms)
        
        # Usa la logica esistente dal metodo originale
        person_targets = self._calculate_balanced_targets(available_people, num_rooms)
        
        print(f"Target per persona: {[(p.name, target) for p, target in person_targets.items()]}")
        print(f"Situazione attuale: {[(p.name, p.total_assignments) for p in available_people]}")
        
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
            
            # Trova persone disponibili oggi
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
            
            # Calcola quante assegnazioni fare oggi
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
        
        # Gestisci stanze rimaste non assegnate
        unassigned_rooms = [room for room in self.rooms if room not in rooms_assigned]
        if unassigned_rooms:
            print(f"\n  FALLBACK per stanze non assegnate: {unassigned_rooms}")
            self._assign_remaining_rooms_fallback(
                unassigned_rooms, available_people, week_number, scheduling_state, chronological_dates
            )
    
    def _calculate_balanced_targets_with_grouping(self, available_people: List[Person], 
                                                unit_weights: Dict[str, int]) -> Dict[Person, int]:
        """
        Calcola target bilanciati considerando i pesi delle unità (gruppi vs singole).
        """
        if not available_people:
            return {}
        
        # Per l'accorpamento con 3 persone, distribuzione semplice
        # Ogni persona dovrebbe ottenere una "unità" di peso appropriato
        total_weight = sum(unit_weights.values())
        base_weight_per_person = total_weight // len(available_people)
        extra_weight = total_weight % len(available_people)
        
        person_targets = {}
        for i, person in enumerate(available_people):
            # Ogni persona ottiene il peso base, più extra se necessario
            target_weight = base_weight_per_person
            if i < extra_weight:
                target_weight += 1
            
            # Converti il peso in numero target (approssimativo)
            person_targets[person] = max(1, target_weight)
        
        return person_targets
    
    def _find_best_date_for_person_and_unit(self, person: Person, unit: Dict, 
                                           available_dates: List[date], week_number: int,
                                           excluded_first_week: Dict[str, List[str]]) -> Optional[date]:
        """
        Trova la migliore data per assegnare un'unità (gruppo o stanza singola) a una persona.
        """
        best_date = None
        best_score = -1
        
        weekly = person.get_weekly_assignment(week_number)
        if not weekly:
            return None
        
        for check_date in available_dates:
            if (person.is_available_on_date(check_date) and 
                not person.has_used_day_in_week(check_date, week_number)):
                
                # Controlla esclusioni prima settimana per tutte le stanze dell'unità
                if week_number == 1 and person.name in excluded_first_week:
                    excluded_rooms = excluded_first_week[person.name]
                    unit_blocked = any(room in excluded_rooms for room in unit['rooms'])
                    if unit_blocked:
                        continue
                
                # Calcola punteggio per questa data
                score = 0.0
                
                # Preferisci giorni feriali
                if check_date.weekday() < 5:
                    score += 30
                else:
                    score += 10
                
                # Bonus per distribuzione temporale
                day_bonuses = {0: 15, 1: 12, 2: 10, 3: 8, 4: 5, 5: 3, 6: 1}
                score += day_bonuses.get(check_date.weekday(), 0)
                
                # Bonus per bilanciamento carico
                total_assignments = person.total_assignments
                if total_assignments <= 2:
                    score += 100
                elif total_assignments <= 4:
                    score += 50
                
                if score > best_score:
                    best_score = score
                    best_date = check_date
        
        return best_date
    
    def _assign_units_with_balancing(self, assignment_units: List[Dict], available_people: List[Person],
                                   chronological_dates: List[date], week_number: int,
                                   excluded_first_week: Dict[str, List[str]], 
                                   scheduling_state: SchedulingState) -> List[RoomAssignment]:
        """
        Assegna le unità (gruppi e stanze singole) bilanciando il carico e la rotazione tra le persone.
        """
        print(f"🎯 Assegnazione intelligente di {len(assignment_units)} unità a {len(available_people)} persone")
        
        assignments_made = []
        
        # Calcola punteggi per ogni combinazione persona-unità
        unit_person_scores = []
        
        for unit in assignment_units:
            for person in available_people:
                # Controlla esclusioni prima settimana
                if week_number == 1 and person.name in excluded_first_week:
                    excluded_rooms = excluded_first_week[person.name]
                    if any(room in excluded_rooms for room in unit['rooms']):
                        continue  # Skip questa combinazione
                
                # Calcola punteggio per questa combinazione
                score = self._calculate_unit_person_score(person, unit, available_people, scheduling_state)
                
                unit_person_scores.append({
                    'unit': unit,
                    'person': person,
                    'score': score
                })
        
        # Ordina per punteggio decrescente
        unit_person_scores.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"📊 Migliori combinazioni:")
        for i, combo in enumerate(unit_person_scores[:6]):  # Mostra solo le prime 6
            unit_name = combo['unit']['name']
            person_name = combo['person'].name
            score = combo['score']
            print(f"  {i+1}. {unit_name} -> {person_name} (score: {score:.0f})")
        
        # Algoritmo di assegnazione con distribuzione temporale intelligente
        assigned_units = set()
        assigned_people = set()
        used_dates = {}  # data -> numero_assegnazioni per evitare concentrazione
        
        for combo in unit_person_scores:
            unit = combo['unit']
            person = combo['person']
            
            # Salta se unità o persona già assegnata
            unit_key = unit['name']
            if unit_key in assigned_units or person.name in assigned_people:
                continue
            
            # Trova la migliore data per questa combinazione considerando la distribuzione temporale
            best_date = self._find_best_date_with_distribution(
                person, unit, chronological_dates, week_number, excluded_first_week, used_dates
            )
            
            if best_date:
                # Assegna tutte le stanze di questa unità alla persona
                for room in unit['rooms']:
                    assignment = RoomAssignment(
                        room=room,
                        person=person,
                        assignment_date=best_date,
                        week_number=week_number,
                        is_grouped=(unit['type'] == 'group'),
                        group_name=unit['name'] if unit['type'] == 'group' else None
                    )
                    scheduling_state.add_assignment(assignment)
                    assignments_made.append(assignment)
                
                # Aggiorna contatori
                assigned_units.add(unit_key)
                assigned_people.add(person.name)
                
                # Aggiorna conteggio date usate
                if best_date not in used_dates:
                    used_dates[best_date] = 0
                used_dates[best_date] += len(unit['rooms'])  # Conta tutte le stanze assegnate
                
                if unit['type'] == 'group':
                    print(f"  ✅ GRUPPO {unit['name']}: {', '.join(unit['rooms'])} -> {person.name} il {best_date.strftime('%a %d')}")
                else:
                    print(f"  ✅ SINGOLA {unit['name']}: -> {person.name} il {best_date.strftime('%a %d')}")
                
                # Se abbiamo assegnato tutto, fermiamoci
                if len(assigned_units) == len(assignment_units):
                    break
        
        # Verifica se ci sono unità non assegnate (non dovrebbe succedere con 3 persone e 3 unità)
        unassigned_units = [unit for unit in assignment_units if unit['name'] not in assigned_units]
        if unassigned_units:
            print(f"⚠️  Unità non assegnate: {[unit['name'] for unit in unassigned_units]}")
            # Fallback: assegna a caso
            for unit in unassigned_units:
                available_for_fallback = [p for p in available_people if p.name not in assigned_people]
                if available_for_fallback:
                    person = available_for_fallback[0]
                    best_date = chronological_dates[0] if chronological_dates else None
                    
                    if best_date:
                        for room in unit['rooms']:
                            assignment = RoomAssignment(
                                room=room,
                                person=person,
                                assignment_date=best_date,
                                week_number=week_number,
                                is_grouped=(unit['type'] == 'group'),
                                group_name=unit['name'] if unit['type'] == 'group' else None
                            )
                            scheduling_state.add_assignment(assignment)
                            assignments_made.append(assignment)
                        
                        print(f"  🆘 FALLBACK {unit['name']}: -> {person.name}")
        
        return assignments_made
    
    def _calculate_unit_person_score(self, person: Person, unit: Dict, all_people: List[Person], 
                                   scheduling_state: SchedulingState) -> float:
        """
        Calcola il punteggio per assegnare un'unità (gruppo o stanza singola) a una persona.
        Considera sia il bilanciamento del carico che la rotazione delle stanze.
        """
        score = 0.0
        
        # 1. BILANCIAMENTO CARICO TOTALE - PESO MASSIMO
        total_assignments = person.total_assignments
        all_loads = [p.total_assignments for p in all_people]
        min_load = min(all_loads)
        max_load = max(all_loads)
        
        # Priorità assoluta per chi ha il carico minimo
        if total_assignments == min_load:
            score += 1000  # Priorità massima
        elif total_assignments == min_load + 1:
            score += 700
        elif total_assignments == min_load + 2:
            score += 400
        else:
            # Forte penalità per chi è già sovraccarico
            load_excess = total_assignments - min_load
            score -= load_excess * 200
        
        # 2. ROTAZIONE STANZE SPECIFICHE
        unit_rooms = unit['rooms']
        
        # Per ogni stanza nell'unità, controlla quanto spesso l'ha fatta questa persona
        room_rotation_bonus = 0
        for room in unit_rooms:
            room_count = person.get_room_count(room)
            
            # Calcola il minimo per questa stanza tra tutte le persone
            room_counts_all = [p.get_room_count(room) for p in all_people]
            min_room_count = min(room_counts_all)
            
            # Bonus per rotazione equa
            if room_count == min_room_count:
                room_rotation_bonus += 300  # Bonus alto per stanza mai/poco fatta
            elif room_count == min_room_count + 1:
                room_rotation_bonus += 150
            else:
                # Penalità per stanze già fatte spesso
                room_rotation_bonus -= (room_count - min_room_count) * 100
        
        score += room_rotation_bonus
        
        # 3. BONUS PER TIPO UNITÀ
        if unit['type'] == 'group':
            # I gruppi sono più "pesanti", quindi dovrebbero andare a chi ha meno carico
            # Il bonus è già incluso nel bilanciamento del carico
            score += 50  # Piccolo bonus per prioritizzare l'assegnazione dei gruppi
        else:
            # Stanze singole sono più flessibili
            score += 20
        
        # 4. BONUS DIVERSITÀ - evita che la stessa persona prenda sempre i gruppi
        # Conta quante volte questa persona ha avuto gruppi in passato
        grouped_assignments = sum(1 for assignment in scheduling_state.assignments 
                                if assignment.person.name == person.name and assignment.is_grouped)
        
        # Penalità crescente per chi ha già avuto molti gruppi
        if unit['type'] == 'group' and grouped_assignments > 0:
            score -= grouped_assignments * 100  # Penalità per evitare sempre la stessa persona
        
        return score
    
    def _find_best_date_with_distribution(self, person: Person, unit: Dict, 
                                         available_dates: List[date], week_number: int,
                                         excluded_first_week: Dict[str, List[str]], 
                                         used_dates: Dict[date, int]) -> Optional[date]:
        """
        Trova la migliore data per un'unità considerando la distribuzione temporale delle assegnazioni.
        Evita di concentrare troppe assegnazioni nello stesso giorno.
        """
        best_date = None
        best_score = -1
        
        weekly = person.get_weekly_assignment(week_number)
        if not weekly:
            return None
        
        print(f"    🗓️  Cercando data per {unit['name']} -> {person.name}")
        print(f"      Date disponibili: {[d.strftime('%a %d') for d in available_dates]}")
        print(f"      Date già usate: {[(d.strftime('%a %d'), count) for d, count in used_dates.items()]}")
        
        for check_date in available_dates:
            if (person.is_available_on_date(check_date) and 
                not person.has_used_day_in_week(check_date, week_number)):
                
                # Controlla esclusioni prima settimana per tutte le stanze dell'unità
                if week_number == 1 and person.name in excluded_first_week:
                    excluded_rooms = excluded_first_week[person.name]
                    unit_blocked = any(room in excluded_rooms for room in unit['rooms'])
                    if unit_blocked:
                        continue
                
                # Calcola punteggio per questa data
                score = 0.0
                
                # 1. DISTRIBUZIONE TEMPORALE - PESO ALTO
                # Forte penalità per giorni già utilizzati
                current_day_load = used_dates.get(check_date, 0)
                if current_day_load == 0:
                    score += 200  # Bonus alto per giorni liberi
                elif current_day_load <= 1:
                    score += 100  # Bonus medio per giorni poco utilizzati
                elif current_day_load <= 2:
                    score += 25   # Piccolo bonus
                else:
                    score -= current_day_load * 50  # Penalità crescente per giorni sovraccarichi
                
                # 2. Preferisci giorni feriali
                if check_date.weekday() < 5:
                    score += 30
                else:
                    score += 10
                
                # 3. Bonus per distribuzione nella settimana
                day_bonuses = {0: 15, 1: 12, 2: 10, 3: 8, 4: 5, 5: 3, 6: 1}
                score += day_bonuses.get(check_date.weekday(), 0)
                
                # 4. Bonus per bilanciamento carico persona
                total_assignments = person.total_assignments
                if total_assignments <= 2:
                    score += 50
                elif total_assignments <= 4:
                    score += 25
                
                # 5. BONUS SPECIALE: evita concentrazione eccessiva
                # Se questo è un gruppo e il giorno ha già altre assegnazioni, penalizza di più
                if unit['type'] == 'group' and current_day_load > 0:
                    score -= 30  # Penalità extra per gruppi in giorni già utilizzati
                
                print(f"        {check_date.strftime('%a %d')}: score {score:.0f} (carico giorno: {current_day_load})")
                
                if score > best_score:
                    best_score = score
                    best_date = check_date
        
        if best_date:
            print(f"      ✅ Scelta: {best_date.strftime('%a %d')} (score: {best_score:.0f})")
        else:
            print(f"      ❌ Nessuna data disponibile")
        
        return best_date