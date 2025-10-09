"""
Generatore di immagini PNG per i calendari dei turni.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import pandas as pd
from typing import Dict, List

from ..utils.constants import MESI_ITALIANI, PNG_CONFIG


class CalendarImageGenerator:
    """Classe per la generazione delle immagini PNG dei calendari."""
    
    def __init__(self):
        """Inizializza il generatore di immagini."""
        self.italian_months = {i: month for i, month in enumerate(MESI_ITALIANI, 1)}
    
    def create_calendar_image(self, schedule_df: pd.DataFrame, month: int, year: int) -> BytesIO:
        """
        Crea un'immagine PNG del calendario mensile con tabella settimanale (colonne = giorni).
        
        Args:
            schedule_df: DataFrame con il piano dei turni
            month: Mese di riferimento
            year: Anno di riferimento
            
        Returns:
            BytesIO buffer contenente l'immagine PNG
        """
        plt.style.use('default')
        
        # Configura la figura con layout tabellare
        fig, ax = plt.subplots(figsize=(PNG_CONFIG['LARGHEZZA'], PNG_CONFIG['ALTEZZA']))
        
        # Titolo
        month_name = self.italian_months[month]
        ax.set_title(
            f'SpazzApp - Piano Turni {month_name} {year}\n', 
            fontsize=PNG_CONFIG['FONT_SIZE_TITOLO'], 
            fontweight='bold', 
            pad=30
        )
        
        # Ottieni le settimane
        weeks_data = schedule_df.groupby('Settimana').first().sort_values('Data_Inizio')
        weeks = weeks_data.index.tolist()
        n_weeks = len(weeks)
        
        # Colori per le persone
        people = schedule_df['Persona'].unique()
        people = [p for p in people if p != "Nessuno disponibile"]
        
        color_map = self._generate_color_map(people)
        
        # Layout tabella: 7 colonne (giorni) + 1 header settimana
        cell_width = 2.2
        cell_height = 1.5
        days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        
        # Header colonne giorni
        self._draw_day_headers(ax, days, cell_width, cell_height, n_weeks)
        
        # Tabella per settimane
        self._draw_weeks_table(
            ax, schedule_df, weeks, n_weeks, cell_width, cell_height, 
            color_map, days
        )
        
        # Legenda per persone
        self._draw_legend(ax, color_map)
        
        # Impostazioni assi
        ax.set_xlim(-3 * cell_width, 7 * cell_width + 1)
        ax.set_ylim(0, (n_weeks + 1) * cell_height)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Salva in BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(
            buffer, 
            format='png', 
            dpi=PNG_CONFIG['DPI'], 
            bbox_inches='tight',
            facecolor=PNG_CONFIG['COLORE_SFONDO'], 
            edgecolor='none', 
            pad_inches=0.5
        )
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def _generate_color_map(self, people: List[str]) -> Dict[str, str]:
        """Genera una mappa di colori per le persone."""
        predefined_colors = [
            '#FF9999', '#66B2FF', '#99FF99', '#FFCC99',
            '#FF99CC', '#99FFCC', '#FFB366', '#B3B3FF'
        ]
        
        color_map = {}
        for i, person in enumerate(people):
            if i < len(predefined_colors):
                color_map[person] = predefined_colors[i]
            else:
                color_map[person] = '#CCCCCC'
        
        color_map["Nessuno disponibile"] = '#FFCCCC'
        return color_map
    
    def _draw_day_headers(self, ax, days: List[str], cell_width: float, 
                         cell_height: float, n_weeks: int):
        """Disegna gli header delle colonne dei giorni."""
        for j, day in enumerate(days):
            rect = patches.Rectangle(
                (j * cell_width, n_weeks * cell_height),
                cell_width, cell_height,
                linewidth=2, 
                edgecolor=PNG_CONFIG['COLORE_BORDO'],
                facecolor='#d4e6f1'
            )
            ax.add_patch(rect)
            ax.text(
                j * cell_width + cell_width/2,
                n_weeks * cell_height + cell_height/2,
                day, 
                ha='center', 
                va='center',
                fontsize=PNG_CONFIG['FONT_SIZE_HEADER'], 
                fontweight='bold'
            )
    
    def _draw_weeks_table(self, ax, schedule_df: pd.DataFrame, weeks: List[str], 
                         n_weeks: int, cell_width: float, cell_height: float,
                         color_map: Dict[str, str], days: List[str]):
        """Disegna la tabella delle settimane."""
        for i, week in enumerate(weeks):
            week_data = schedule_df[schedule_df['Settimana'] == week]
            periodo = week_data.iloc[0]['Periodo']
            
            # Header settimana (sinistra)
            self._draw_week_header(
                ax, week, periodo, i, n_weeks, cell_width, cell_height
            )
            
            # Crea dizionario giorno -> assegnazioni per questa settimana
            week_assignments_by_day = self._group_assignments_by_day(week_data)
            
            # Riempi celle per ogni giorno
            self._draw_day_cells(
                ax, week_assignments_by_day, days, i, n_weeks, 
                cell_width, cell_height, color_map
            )
    
    def _draw_week_header(self, ax, week: str, periodo: str, week_index: int,
                         n_weeks: int, cell_width: float, cell_height: float):
        """Disegna l'header di una settimana."""
        rect = patches.Rectangle(
            (-2.5 * cell_width, (n_weeks - week_index - 1) * cell_height),
            2.5 * cell_width, cell_height,
            linewidth=2, 
            edgecolor=PNG_CONFIG['COLORE_BORDO'],
            facecolor=PNG_CONFIG['COLORE_ALTERNATIVO']
        )
        ax.add_patch(rect)
        ax.text(
            -1.25 * cell_width,
            (n_weeks - week_index - 1) * cell_height + cell_height/2,
            f'{week}\n({periodo})', 
            ha='center', 
            va='center',
            fontsize=10, 
            fontweight='bold'
        )
    
    def _group_assignments_by_day(self, week_data: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Raggruppa le assegnazioni per giorno della settimana."""
        week_assignments_by_day = {}
        for _, row in week_data.iterrows():
            day_name = row['Giorno_Settimana']
            if day_name not in week_assignments_by_day:
                week_assignments_by_day[day_name] = []
            
            week_assignments_by_day[day_name].append({
                'person': row['Persona'],
                'room': row['Stanza'],
                'date': row['Data_Specifica'].strftime('%d/%m')
            })
        return week_assignments_by_day
    
    def _draw_day_cells(self, ax, week_assignments_by_day: Dict[str, List[Dict]],
                       days: List[str], week_index: int, n_weeks: int,
                       cell_width: float, cell_height: float, 
                       color_map: Dict[str, str]):
        """Disegna le celle per ogni giorno della settimana."""
        for j, day in enumerate(days):
            # Cella base
            rect = patches.Rectangle(
                (j * cell_width, (n_weeks - week_index - 1) * cell_height),
                cell_width, cell_height,
                linewidth=1, 
                edgecolor=PNG_CONFIG['COLORE_BORDO'],
                facecolor=PNG_CONFIG['COLORE_SFONDO']
            )
            ax.add_patch(rect)
            
            # Aggiungi le assegnazioni per questo giorno
            if day in week_assignments_by_day:
                assignments = week_assignments_by_day[day]
                self._draw_assignments_in_cell(
                    ax, assignments, j, week_index, n_weeks,
                    cell_width, cell_height, color_map
                )
    
    def _draw_assignments_in_cell(self, ax, assignments: List[Dict], day_index: int,
                                 week_index: int, n_weeks: int, cell_width: float,
                                 cell_height: float, color_map: Dict[str, str]):
        """Disegna le assegnazioni all'interno di una cella."""
        display_lines = []
        
        for assignment in assignments:
            person = assignment['person']
            room = assignment['room']
            date = assignment['date']
            
            if person == "Nessuno disponibile":
                display_lines.append(f"X {room}")
            else:
                display_lines.append(f"{person}")
                display_lines.append(f"{room}")
                display_lines.append(f"{date}")
        
        if display_lines:
            display_text = '\n'.join(display_lines[:4])  # Max 4 righe
            
            # Colore basato sulla prima persona assegnata
            first_person = assignments[0]['person']
            color = color_map.get(first_person, '#ffffff')
            
            # Aggiungi sfondo colorato
            colored_rect = patches.Rectangle(
                (day_index * cell_width + 0.05, (n_weeks - week_index - 1) * cell_height + 0.05),
                cell_width - 0.1, cell_height - 0.1,
                linewidth=0, facecolor=color, alpha=0.3
            )
            ax.add_patch(colored_rect)
            
            text_color = '#8B0000' if first_person == "Nessuno disponibile" else 'black'
            font_size = 8 if len(display_lines) > 2 else 9
            
            ax.text(
                day_index * cell_width + cell_width/2,
                (n_weeks - week_index - 1) * cell_height + cell_height/2,
                display_text, 
                ha='center', 
                va='center',
                fontsize=font_size, 
                fontweight='bold',
                color=text_color
            )
    
    def _draw_legend(self, ax, color_map: Dict[str, str]):
        """Disegna la legenda delle persone."""
        legend_elements = []
        for person, color in color_map.items():
            if person != "Nessuno disponibile":
                legend_elements.append(patches.Patch(color=color, label=person))
        
        if legend_elements:
            ax.legend(
                handles=legend_elements, 
                loc='upper left',
                bbox_to_anchor=(1.02, 1), 
                fontsize=11,
                title="Persone", 
                title_fontsize=12
            )