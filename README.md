# 🏠 SpazzApp - Gestione Turni di Pulizia Intelligente

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**SpazzApp** è un'applicazione web intelligente per la gestione automatica dei turni di pulizia domestici. Utilizza algoritmi avanzati per distribuire equamente le pulizie tra i coinquilini, garantendo rotazione delle stanze e bilanciamento del carico di lavoro.

![SpazzApp Demo](docs/demo-screenshot.png)

## ✨ Caratteristiche Principali

### 🎯 **Distribuzione Intelligente**

- **Rotazione automatica**: Evita che la stessa persona pulisca sempre la stessa stanza
- **Bilanciamento del carico**: Distribuzione equa del lavoro tra tutti i partecipanti
- **Gestione assenze**: Redistribuisce automaticamente il lavoro quando qualcuno è assente
- **Priorità giorni feriali**: Preferisce i giorni lun-ven per le assegnazioni

### 📅 **Gestione Avanzata**

- **Pianificazione mensile**: Genera automaticamente i turni per un mese completo
- **Esclusioni personalizzate**: Permette di escludere specifiche stanze per persona nella prima settimana
- **Gestione assenze**: Interfaccia intuitiva per inserire periodi di assenza
- **Visualizzazione cronologica**: Mostra i turni ordinati per data

### 🎨 **Interfaccia Utente**

- **Multi-pagina**: Navigazione fluida tra configurazione, generazione turni ed export
- **Design responsive**: Ottimizzato per desktop e mobile
- **Esportazione PNG**: Genera calendari visivi stampabili
- **Statistiche dettagliate**: Mostra distribuzione stanze e giorni per persona

## 🚀 Installazione e Avvio

### Prerequisiti

- Python 3.8 o superiore
- pip (gestore pacchetti Python)

### 1. Clona il repository

```bash
git clone https://github.com/GiuseppeBellamacina/SpazzApp.git
cd SpazzApp
```

### 2. Crea ambiente virtuale (consigliato)

```bash
# Windows
python -m venv .venv
.venv\\Scripts\\activate

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 4. Avvia l'applicazione

```bash
streamlit run app.py
```

L'applicazione sarà accessibile su `http://localhost:8501`

## 📖 Guida all'Uso

### 1. ⚙️ **Configurazione**

1. Inserisci i **nomi dei partecipanti** (uno per riga)
2. Seleziona **mese e anno** per la pianificazione
3. Aggiungi eventuali **assenze** usando il selettore di date
4. Configura **esclusioni per la prima settimana** se necessario

### 2. 🎲 **Generazione Turni**

1. Vai alla pagina "Generazione Turni"
2. Clicca su **"Genera Turni Intelligenti"**
3. Visualizza la **tabella dei turni** generati
4. Controlla le **statistiche di distribuzione**

### 3. 📸 **Export PNG**

1. Vai alla pagina "Export PNG"
2. Clicca su **"Genera Calendario PNG"**
3. **Scarica** l'immagine del calendario generato

## 🏗️ Architettura del Progetto

```
SpazzApp/
├── app.py                 # Entry point principale
├── requirements.txt       # Dipendenze Python
├── pages/                 # Pagine Streamlit
│   ├── configurazione.py  # Configurazione utente
│   ├── turni.py          # Generazione turni
│   └── export.py         # Export calendario PNG
├── src/                   # Codice sorgente
│   ├── core/             # Logica principale
│   │   ├── scheduler.py   # Algoritmo di scheduling
│   │   └── models.py     # Modelli dati
│   ├── ui/               # Componenti interfaccia
│   │   ├── components.py  # Componenti UI riutilizzabili
│   │   └── image_generator.py # Generazione immagini
│   └── utils/            # Utilità
│       ├── constants.py   # Costanti applicazione
│       └── helpers.py    # Funzioni helper
└── .streamlit/           # Configurazione Streamlit
    └── config.toml
```

## 🧠 Algoritmo di Scheduling

### Principi Base

1. **Distribuzione Cronologica**: Le assegnazioni sono distribuite sui giorni della settimana in ordine temporale
2. **Rotazione delle Stanze**: Priorità assoluta a chi non ha mai pulito una specifica stanza
3. **Bilanciamento del Carico**: Evita sovraccarico di una singola persona
4. **Gestione Dinamica**: Si adatta automaticamente ad assenze e vincoli

### Algoritmo di Scoring

Il sistema assegna punteggi basati su:

- **Rotazione stanza** (+400 punti per stanza mai pulita)
- **Bilanciamento carico** (+600 punti per chi ha il carico minimo)
- **Giorni feriali** (+30 punti lun-ven, +10 weekend)
- **Distribuzione temporale** (bonus per distribuzione equa)

### Gestione Vincoli

- **Esclusioni prima settimana**: Rispetta preferenze specifiche
- **Limite giornaliero**: Massimo 3 assegnazioni per giorno
- **Assenze**: Redistribuisce automaticamente il carico
- **Target dinamici**: Calcola obiettivi settimanali considerando lo storico

## 🛠️ Tecnologie Utilizzate

- **[Streamlit](https://streamlit.io/)**: Framework per web app in Python
- **[Pandas](https://pandas.pydata.org/)**: Manipolazione e analisi dati
- **[Matplotlib](https://matplotlib.org/)**: Generazione grafici e calendari
- **[Pillow](https://pillow.readthedocs.io/)**: Manipolazione immagini
- **Python 3.8+**: Linguaggio di programmazione

## 📊 Esempi di Output

### Tabella Turni

| Settimana   | Periodo       | Stanza | Persona | Giorno  | Data  |
| ----------- | ------------- | ------ | ------- | ------- | ----- |
| Settimana 1 | 01/11 - 07/11 | Bagno  | Alice   | Lunedì  | 04/11 |
| Settimana 1 | 01/11 - 07/11 | Cucina | Bob     | Martedì | 05/11 |

### Statistiche Distribuzione

- **Per Persona**: Alice (5 turni), Bob (4 turni), Charlie (5 turni)
- **Per Stanza**: Bagno (4 assegnazioni), Cucina (5 assegnazioni)
- **Per Giorno**: Lunedì (3), Martedì (4), Mercoledì (3)

## 🤝 Contribuire

Le contribuzioni sono benvenute! Per contribuire:

1. Fork del progetto
2. Crea un branch per la feature (`git checkout -b feature/NuovaFeature`)
3. Commit delle modifiche (`git commit -m 'Aggiunge NuovaFeature'`)
4. Push del branch (`git push origin feature/NuovaFeature`)
5. Apri una Pull Request

## 🐛 Segnalazione Bug

Per segnalare bug o richiedere nuove funzionalità, apri un [issue](https://github.com/GiuseppeBellamacina/SpazzApp/issues).

## 📝 Changelog

### v2.0.0 - Riarchitettura Completa

- ✅ Nuova architettura object-oriented
- ✅ Algoritmo di bilanciamento migliorato
- ✅ Gestione avanzata delle assenze
- ✅ Interface multi-pagina
- ✅ Export calendario PNG

### v1.0.0 - Release Iniziale

- ✅ Generazione turni base
- ✅ Gestione assenze semplice
- ✅ Interfaccia single-page

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 👨‍💻 Autore

**Giuseppe Bellamacina**

- GitHub: [@GiuseppeBellamacina](https://github.com/GiuseppeBellamacina)

---

⭐ Se SpazzApp ti è utile, lascia una stella su GitHub!

## 💡 Roadmap Future

- [ ] 📱 App mobile nativa
- [ ] 🔔 Notifiche automatiche
- [ ] 📈 Analytics e statistiche avanzate
- [ ] 🌐 Versione multi-lingua
- [ ] 🏠 Gestione multiple case
- [ ] 📧 Invio turni via email
- [ ] 🎨 Temi personalizzabili
- [ ] 💾 Backup e sincronizzazione cloud
