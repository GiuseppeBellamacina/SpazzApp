# 🚀 Deploy su Streamlit Cloud

## Passo 1: Preparazione del repository

1. Carica tutti i file su GitHub:
   - `app.py` (file principale dell'applicazione)
   - `requirements.txt` (dipendenze)
   - `README.md` (documentazione)
   - `.streamlit/config.toml` (configurazione Streamlit)

## Passo 2: Deploy su Streamlit Cloud

1. Vai su [share.streamlit.io](https://share.streamlit.io/)
2. Accedi con il tuo account GitHub
3. Clicca su "New app"
4. Seleziona il repository GitHub dove hai caricato i file
5. Imposta:
   - **Branch**: main (o il branch dove hai i file)
   - **Main file path**: app.py
   - **App URL**: scegli un nome per la tua app (es: turni-pulizie-rebecca)

## Passo 3: Configurazione (opzionale)

Se necessario, puoi aggiungere variabili d'ambiente o secrets nel pannello di controllo dell'app.

## Passo 4: Verifica

Dopo il deploy, l'app sarà accessibile all'URL:
`https://[nome-app]-[username].streamlit.app`

## Alternative di Deploy

### Heroku

1. Aggiungi un file `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```
2. Segui la guida di deploy di Heroku

### Railway

1. Connetti il repository GitHub
2. Railway rileverà automaticamente che è un'app Python
3. L'app sarà deployata automaticamente

### Render

1. Connetti il repository GitHub
2. Scegli "Web Service"
3. Imposta il comando di build: `pip install -r requirements.txt`
4. Imposta il comando di start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

## 📱 Utilizzo Mobile

L'applicazione è ottimizzata anche per dispositivi mobili grazie al responsive design di Streamlit.

## 🔧 Manutenzione

Per aggiornare l'applicazione:

1. Modifica i file nel repository GitHub
2. Fai commit e push
3. L'app su Streamlit Cloud si aggiornerà automaticamente
