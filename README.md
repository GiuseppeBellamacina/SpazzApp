# 🏠 SpazzApp 🧹

Un sistema intelligente per la gestione automatica dei turni di pulizia domestica, con algoritmi di bilanciamento e ottimizzazione per massimizzare l'efficienza e ridurre i conflitti.

## ✨ Caratteristiche Principali

### 🎯 Algoritmo Intelligente

- **Distribuzione flessibile**: Giorni assegnabili da Lunedì a Domenica
- **Bilanciamento automatico**: Distribuzione equa del carico di lavoro
- **Evita conflitti**: Prevenzione sovrapposizioni stesso giorno
- **Priorità persone vincolate**: Favorisce chi ha pochi giorni disponibili
- **Rotazione mensile**: Evita ripetizioni stanza/persona nello stesso mese
- **Gestione assenze**: Sistema avanzato per periodi di indisponibilità

### 🖥️ Interfaccia Utente

- **Streamlit web app**: Interfaccia moderna e intuitiva
- **Configurazione sidebar**: Controlli centralizzati e facili da usare
- **Visualizzazione cronologica**: Piano turni organizzato per data
- **Export PNG**: Calendario scaricabile in formato immagine

### ⚙️ Configurazioni Avanzate

- **Prima settimana personalizzabile**: Esclusioni e priorità specifiche
- **Gestione assenze**: Periodi di indisponibilità per persona
- **Mesi in italiano**: Localizzazione completa dell'interfaccia
- **Auto-selezione periodo**: Mese e anno correnti pre-selezionati

## 🚀 Come Iniziare

### Prerequisiti

```bash
Python 3.8+
pip install -r requirements.txt
```

### Installazione

```bash
git clone <repository-url>
cd SpazzApp
pip install -r requirements.txt
```

### Avvio

**Modalità principale (entry point principale):**

```bash
streamlit run app.py
```

L'app sarà disponibile su `http://localhost:8501`

## 📱 Utilizzo

1. **Configura i coinquilini**: Inserisci i nomi nella sidebar (uno per riga)
2. **Seleziona periodo**: Scegli mese e anno (già preselezionati su quelli correnti)
3. **Imposta esclusioni**: Configura eventuali esclusioni per la prima settimana
4. **Definisci priorità**: Riordina le stanze per priorità nella prima settimana
5. **Aggiungi assenze**: Registra periodi di indisponibilità
6. **Genera turni**: Clicca il pulsante per creare il piano automaticamente
7. **Scarica PNG**: Esporta il calendario in formato immagine

## 🏗️ Architettura Modulare (Refactored v7.1.0)

Il progetto è stato completamente refactorizzato in una struttura modulare per migliorare manutenibilità e scalabilità:

```
SpazzApp/
├── app.py                 # Entry point principale
├── src/                  # Codice sorgente modulare
│   ├── __init__.py
│   ├── core/            # Logica di business
│   │   ├── __init__.py
│   │   └── scheduler.py # Algoritmo scheduling principale
│   ├── ui/              # Interfaccia utente
│   │   ├── __init__.py
│   │   ├── streamlit_app.py    # App Streamlit principale
│   │   ├── components.py       # Componenti UI (sidebar, display)
│   │   └── image_generator.py  # Generazione PNG
│   └── utils/           # Utilità e costanti
│       ├── __init__.py
│       ├── constants.py # Costanti di sistema
│       └── helpers.py   # Funzioni di supporto
└── requirements.txt
```

### Componenti Principali

#### `src.core.scheduler.CleaningScheduler`

- **Algoritmo core**: Logica di scheduling intelligente
- **Bilanciamento**: Sistema di punteggi multi-fattore
- **Ottimizzazione**: Distribuzione equa tra persone e giorni

#### `src.ui.streamlit_app.StreamlitApp`

- **App principale**: Orchestrazione dell'interfaccia
- **Configurazione**: Setup pagina e stili
- **Coordinamento**: Integrazione tra componenti

#### `src.ui.components`

- **SidebarManager**: Gestione configurazione sidebar
- **ScheduleDisplayManager**: Visualizzazione cronologica turni

#### `src.ui.image_generator.CalendarImageGenerator`

- **Export PNG**: Generazione calendari immagine
- **Layout avanzato**: Tabelle settimanali con colonne giorni
- **Personalizzazione**: Colori e stili configurabili

#### `src.utils`

- **constants.py**: Costanti di sistema e configurazione
- **helpers.py**: Funzioni di supporto e utilities

### Sistema di Punteggi

```python
# Pesi algoritmo (in constants.py)
ALGORITMO_CONFIG = {
    'PESO_BILANCIAMENTO': 0.5,      # 50% - Distribuzione equa carico
    'PESO_DISTRIBUZIONE_GIORNI': 0.3,  # 30% - Evita concentrazioni giornaliere
    'PESO_QUALITA_ASSEGNAZIONE': 0.2   # 20% - Preferenze giorni/persone
}
```

### Stanze Gestite (Configurabili)

- 🚿 **Bagno**
- 🍳 **Cucina**
- 🌿 **Veranda**
- 🚪 **Corridoio**

## 📊 Metriche e Ottimizzazioni

### Fattori di Scoring

1. **Persone vincolate** (max priorità): ≤2 giorni disponibili
2. **Distribuzione giorni**: Preferenza Lun-Ven, evita weekend
3. **Bilanciamento carico**: Equalizza assegnazioni per persona
4. **Rotazione mensile**: Evita ripetizioni stanza/persona
5. **Conflitti giornalieri**: Massimo una assegnazione per giorno

### Algoritmo di Fallback

Sistema robusto che gestisce edge cases:

- Persone assenti intere settimane
- Configurazioni con vincoli estremi
- Mesi con poche persone disponibili
- Stanze con alta priorità

## 🎨 Personalizzazione

### Stanze

Modifica la lista in `src/utils/constants.py`:

```python
STANZE_DEFAULT = ['Bagno', 'Cucina', 'Soggiorno', 'Camera']
```

### Algoritmo

Regola i pesi in `src/utils/constants.py`:

```python
ALGORITMO_CONFIG = {
    'PESO_BILANCIAMENTO': 0.6,  # Maggiore focus su bilanciamento
    'EVITA_WEEKEND': False      # Permetti weekend
}
```

### Colori PNG

Modifica in `src/ui/image_generator.py`:

```python
predefined_colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99']
```

### Stili CSS

Personalizza in `src/utils/constants.py`:

```python
CSS_STYLES = """<style>...</style>"""
```

## 🔧 Configurazione Avanzata

### Import Modulare

```python
# Importa singoli componenti
from src.core.scheduler import CleaningScheduler
from src.ui.image_generator import CalendarImageGenerator
from src.utils.helpers import get_month_weeks

# Oppure usa l'app completa
from src.ui.streamlit_app import create_app
```

### Estensibilità

La nuova architettura modulare permette:

- Aggiunta facile di nuovi algoritmi in `src/core/`
- Componenti UI riutilizzabili in `src/ui/`
- Utilities condivise in `src/utils/`

## 📈 Roadmap

- [x] **Architettura modulare**: Refactor completo della struttura ✅
- [ ] **Database persistence**: Salvataggio configurazioni
- [ ] **Multi-appartamento**: Gestione più case contemporaneamente
- [ ] **Notifiche**: Promemoria automatici via email/SMS
- [ ] **Analytics**: Dashboard con statistiche dettagliate
- [ ] **API REST**: Integrazione con app esterne
- [ ] **Mobile app**: Versione nativa per smartphone
- [ ] **Plugin system**: Algoritmi personalizzabili

## 🤝 Contribuire

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/nuova-funzionalità`)
3. Commit modifiche (`git commit -am 'Aggiunge nuova funzionalità'`)
4. Push branch (`git push origin feature/nuova-funzionalità`)
5. Crea Pull Request

### Struttura Contributi

- **Core Logic**: Modifiche in `src/core/`
- **UI Components**: Miglioramenti in `src/ui/`
- **Utilities**: Helpers in `src/utils/`

## 📄 Licenza

Progetto sotto licenza MIT. Vedi file `LICENSE` per dettagli.

## 🆘 Supporto

Per bug report, feature request o domande:

- Apri una issue su GitHub
- Contatta il maintainer

## 🔄 Changelog

### v7.1.0 - Refactor Modulare

- ✨ **NEW**: Architettura completamente modulare
- ♻️ **REFACTOR**: Separazione logica business/UI/utils
- 📁 **STRUCTURE**: Organizzazione in cartelle logiche
- 🎯 **ENTRY POINTS**: `app.py` (compatibile) + `app_new.py` (modulare)

### v7.0.x - Precedenti

- Sistema monolitico con tutte le funzionalità integrate
- Algoritmi avanzati di distribuzione e bilanciamento
- Export PNG e gestione assenze completa

---

_Sviluppato con ❤️ per semplificare la gestione domestica_
