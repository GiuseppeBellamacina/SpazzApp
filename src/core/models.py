"""
Modelli dati per il sistema di scheduling delle pulizie.
"""

from datetime import date, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field


@dataclass
class WeeklyAssignment:
    """Rappresenta le assegnazioni di una persona in una settimana specifica."""
    week_number: int
    week_start: date
    week_end: date
    assignments: Dict[str, date] = field(default_factory=dict)  # stanza -> data assegnazione
    
    def add_assignment(self, room: str, assignment_date: date):
        """Aggiunge un'assegnazione stanza-data per questa settimana."""
        self.assignments[room] = assignment_date
    
    def get_assigned_rooms(self) -> Set[str]:
        """Ritorna le stanze assegnate in questa settimana."""
        return set(self.assignments.keys())
    
    def get_assigned_dates(self) -> Set[date]:
        """Ritorna le date in cui la persona ha assegnazioni."""
        return set(self.assignments.values())
    
    def has_room(self, room: str) -> bool:
        """Controlla se la persona ha questa stanza assegnata nella settimana."""
        return room in self.assignments
    
    def is_available_on_date(self, check_date: date, absences: List[date]) -> bool:
        """Controlla se la persona è disponibile in una data specifica."""
        return check_date not in absences and self.week_start <= check_date <= self.week_end


class Person:
    """Rappresenta una persona nel sistema di scheduling."""
    
    def __init__(self, name: str):
        self.name = name
        self.total_assignments = 0
        self.room_assignments = {}  # stanza -> numero assegnazioni totali
        self.weekly_data = {}  # week_number -> WeeklyAssignment
        self.absences = []  # Lista di date di assenza
        
    def initialize_rooms(self, rooms: List[str]):
        """Inizializza il conteggio per tutte le stanze."""
        for room in rooms:
            self.room_assignments[room] = 0
    
    def add_weekly_assignment(self, week_assignment: WeeklyAssignment):
        """Aggiunge dati per una settimana specifica."""
        self.weekly_data[week_assignment.week_number] = week_assignment
        
        # Aggiorna contatori
        for room in week_assignment.get_assigned_rooms():
            self.room_assignments[room] += 1
            self.total_assignments += 1
    
    def get_room_count(self, room: str) -> int:
        """Ritorna quante volte ha pulito una stanza specifica."""
        return self.room_assignments.get(room, 0)
    
    def get_weekly_assignment(self, week_number: int) -> Optional[WeeklyAssignment]:
        """Ritorna i dati di una settimana specifica."""
        return self.weekly_data.get(week_number)
    
    def is_available_on_date(self, check_date: date) -> bool:
        """Controlla disponibilità in una data."""
        return check_date not in self.absences
    
    def get_available_days_in_week(self, week_start: date, week_end: date) -> List[date]:
        """Ritorna i giorni disponibili in una settimana, prioritizzando i feriali."""
        available_days = []
        current_date = week_start
        
        while current_date <= week_end:
            if self.is_available_on_date(current_date):
                available_days.append(current_date)
            current_date += timedelta(days=1)
        
        # Prioritizza giorni feriali
        workdays = [d for d in available_days if d.weekday() < 5]  # lun-ven
        weekends = [d for d in available_days if d.weekday() >= 5]  # sab-dom
        
        return workdays + weekends
    
    def has_used_day_in_week(self, check_date: date, week_number: int) -> bool:
        """Controlla se ha già un'assegnazione in quella data nella settimana."""
        weekly = self.get_weekly_assignment(week_number)
        if not weekly:
            return False
        return check_date in weekly.get_assigned_dates()
    
    def get_rooms_never_cleaned(self, all_rooms: List[str]) -> List[str]:
        """Ritorna stanze che non ha mai pulito."""
        return [room for room in all_rooms if self.get_room_count(room) == 0]
    
    def get_least_cleaned_rooms(self, all_rooms: List[str]) -> List[str]:
        """Ritorna stanze pulite meno volte, ordinate per frequenza crescente."""
        room_counts = [(self.get_room_count(room), room) for room in all_rooms]
        room_counts.sort(key=lambda x: x[0])  # ordina per count crescente
        return [room for count, room in room_counts]
    
    def __str__(self):
        return f"Person({self.name}, total: {self.total_assignments}, rooms: {self.room_assignments})"
    
    def __repr__(self):
        return self.__str__()


@dataclass
class RoomAssignment:
    """Rappresenta l'assegnazione di una stanza in una data specifica."""
    room: str
    person: Person
    assignment_date: date
    week_number: int
    
    def __str__(self):
        return f"{self.room} -> {self.person.name} ({self.assignment_date.strftime('%a %d/%m')})"


class SchedulingState:
    """Mantiene lo stato durante il processo di scheduling."""
    
    def __init__(self, people: List[Person], rooms: List[str]):
        self.people = {person.name: person for person in people}
        self.rooms = rooms
        self.assignments = []  # Lista di RoomAssignment
        self.daily_assignments = {}  # date -> List[RoomAssignment]
        
    def add_assignment(self, assignment: RoomAssignment):
        """Aggiunge un'assegnazione al sistema."""
        self.assignments.append(assignment)
        
        # Aggiorna daily_assignments
        date_key = assignment.assignment_date
        if date_key not in self.daily_assignments:
            self.daily_assignments[date_key] = []
        self.daily_assignments[date_key].append(assignment)
        
        # Aggiorna la persona
        weekly_assignment = assignment.person.get_weekly_assignment(assignment.week_number)
        if weekly_assignment:
            weekly_assignment.add_assignment(assignment.room, assignment.assignment_date)
        
        # Aggiorna contatori persona
        assignment.person.room_assignments[assignment.room] += 1
        assignment.person.total_assignments += 1
    
    def get_assignments_for_date(self, check_date: date) -> List[RoomAssignment]:
        """Ritorna tutte le assegnazioni per una data."""
        return self.daily_assignments.get(check_date, [])
    
    def get_assignments_count_for_date(self, check_date: date) -> int:
        """Conta quante assegnazioni ci sono in una data."""
        return len(self.get_assignments_for_date(check_date))
    
    def is_room_assigned_in_week(self, room: str, week_number: int) -> bool:
        """Controlla se una stanza è già assegnata in una settimana."""
        for assignment in self.assignments:
            if assignment.room == room and assignment.week_number == week_number:
                return True
        return False
    
    def get_person_assignments_in_week(self, person_name: str, week_number: int) -> List[RoomAssignment]:
        """Ritorna tutte le assegnazioni di una persona in una settimana."""
        return [a for a in self.assignments 
                if a.person.name == person_name and a.week_number == week_number]
    
    def get_room_assignment_distribution(self) -> Dict[str, Dict[str, int]]:
        """Ritorna la distribuzione stanza -> persona -> count."""
        distribution = {}
        for room in self.rooms:
            distribution[room] = {}
            for person_name in self.people.keys():
                distribution[room][person_name] = 0
        
        for assignment in self.assignments:
            distribution[assignment.room][assignment.person.name] += 1
            
        return distribution
    
    def print_summary(self):
        """Stampa un riassunto dello stato attuale."""
        print("\n=== STATO SCHEDULING ===")
        for person in self.people.values():
            print(f"{person.name}: {person.total_assignments} totali - {person.room_assignments}")
        
        print(f"\nAssegnazioni totali: {len(self.assignments)}")
        print(f"Giorni con assegnazioni: {len(self.daily_assignments)}")