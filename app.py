"""
SpazzApp - Gestione Turni di Pulizia Intelligente
"""

from src.ui.streamlit_app import create_app

def main():
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()

# TODO: se 2 persone lavorano lo stesso giorno, il png non le mostra entrambe (bug nella generazione immagine)
# TODO: se ci sono 2 persone e 4 stanze, non le distribuisce bene (bug nella logica di assegnazione)
# TODO: fare un config più bello con multipagina
# TODO: non fare resettare pagina dopo il download dell'immagine
# TODO: fare il deploy online
