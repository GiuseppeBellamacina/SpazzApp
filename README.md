# 🏠 Gestione Turni Pulizie

Un'applicazione Streamlit per gestire automaticamente i turni di pulizia tra coinquilini.

## 🌟 Caratteristiche

- **Stanze predefinite**: Bagno, Cucina, Veranda, Corridoio
- **Generazione automatica turni**: Turni settimanali per un mese intero
- **Rotazione intelligente**: Evita di assegnare la stessa stanza alla stessa persona in settimane consecutive
- **Gestione assenze**: Possibilità di inserire periodi di assenza per ciascun coinquilino
- **Interfaccia intuitiva**: Design accattivante con Streamlit
- **Esportazione**: Scarica i turni in formato CSV

## 🚀 Come utilizzare

### Installazione locale

1. Clona o scarica il progetto
2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
3. Avvia l'applicazione:
   ```bash
   streamlit run app.py
   ```

### Utilizzo dell'applicazione

1. **Inserisci i coinquilini**: Nella barra laterale, inserisci i nomi dei coinquilini (uno per riga)
2. **Seleziona il periodo**: Scegli mese e anno per cui generare i turni
3. **Aggiungi assenze** (opzionale):
   - Seleziona la persona
   - Inserisci data inizio e fine assenza
   - Clicca "Aggiungi Assenza"
4. **Genera i turni**: Clicca il pulsante "Genera Turni"
5. **Visualizza e scarica**: Visualizza i turni generati e scarica il file CSV se necessario

## 🔧 Deploy online

### Streamlit Cloud

1. Carica il progetto su GitHub
2. Vai su [share.streamlit.io](https://share.streamlit.io/)
3. Collega il tuo repository GitHub
4. L'app sarà disponibile online automaticamente

### Altre piattaforme

L'applicazione può essere deployata su:

- Heroku
- Railway
- Render
- Vercel (con configurazione appropriata)

## 📋 Funzionalità dell'algoritmo

- **Distribuzione equa**: L'algoritmo cerca di distribuire equamente i turni tra tutti i coinquilini
- **Rotazione settimanale**: Ogni settimana vengono assegnate tutte e 4 le stanze
- **Evita ripetizioni**: Una persona che ha pulito una stanza in una settimana, non la rifarà la settimana successiva (quando possibile)
- **Gestione conflitti**: Se una persona non è disponibile, viene automaticamente sostituita
- **Backup assignment**: In caso di conflitti irrisolvibili, l'algoritmo trova la migliore soluzione disponibile

## 🎨 Personalizzazione

Puoi facilmente personalizzare:

- Le stanze da pulire (modifica la lista `self.rooms` nella classe `CleaningScheduler`)
- I colori e lo stile dell'interfaccia (modifica la sezione CSS)
- La logica di assegnazione (modifica il metodo `generate_schedule`)

## 📝 Note tecniche

- Utilizza `pandas` per la gestione dei dati
- Interfaccia costruita con `streamlit`
- Algoritmo di assegnazione basato su randomizzazione controllata
- Gestione delle date con il modulo `datetime`

## 🐛 Troubleshooting

Se riscontri problemi:

1. Assicurati di aver installato tutte le dipendenze
2. Verifica che la versione di Python sia >= 3.7
3. Controlla che le date di assenza siano nel formato corretto
4. In caso di errori, ricarica la pagina dell'applicazione
