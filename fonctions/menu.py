import keyboard
import pymsgbox

from fonctions.detection_page import detecter_page_actuelle
from fonctions.calendrier_du_championnat.Fonctions_detection_Combats import traiter_tous_les_combats


def afficher_aide():
    """Affiche une fenêtre d'aide rappelant les raccourcis."""
    message = (
        "F1 : Afficher l'aide\n"
        "F3 : Lancer la capture automatique\n"
        "ESC : Quitter le programme"
    )
    pymsgbox.alert(message, title="Aide")


def lancer_capture(logger, window):
    """Lance la capture automatique des combats."""
    page = detecter_page_actuelle(logger, window)
    if not page or page.get("page") != "calendrier_du_championnat":
        logger.warning("⚠️ Capture impossible : pas sur le calendrier du championnat.")
        pymsgbox.alert(
            "Impossible de lancer la capture : ouvrez le calendrier du championnat.",
            title="Erreur"
        )
        return

    total = traiter_tous_les_combats(logger, window)
    pymsgbox.alert(
        f"Capture terminée. Combats traités : {total}",
        title="Fin de la capture"
    )


def boucle_principale(logger, window):
    """Boucle d'attente principale pour les raccourcis clavier."""
    logger.info("⌨️  Appuyez sur F1 pour l'aide, F3 pour lancer la capture, ESC pour quitter.")
    keyboard.add_hotkey('f1', afficher_aide)
    keyboard.add_hotkey('f3', lambda: lancer_capture(logger, window))
    keyboard.wait('esc')
    logger.info("🚪 Touche ESC détectée : arrêt du programme.")
