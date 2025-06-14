import keyboard
import pymsgbox

from configuration.log_config import toggle_debug
from fonctions.overlay import Overlay

from fonctions.detection_page import detecter_page_actuelle
from fonctions.calendrier_du_championnat.Fonctions_detection_Combats import traiter_tous_les_combats


def afficher_aide(logger=None):
    """Affiche une fenêtre d'aide rappelant les raccourcis."""
    if logger:
        logger.info("Affichage de l'aide utilisateur")
    message = (
        "F1 : Afficher l'aide\n"
        "F3 : Lancer la capture automatique\n"
        "F9 : Basculer le mode debug\n"
        "F8 : Afficher/Masquer l'overlay\n"
        "ESC : Quitter le programme"
    )
    pymsgbox.alert(message, title="Aide")


def lancer_capture(logger, window, overlay: Overlay):
    """Lance la capture automatique des combats."""
    logger.info("Demande de lancement de la capture")
    overlay.set_phase("Détection de la page")
    page = detecter_page_actuelle(logger, window)
    if not page or page.get("page") != "calendrier_du_championnat":
        logger.warning("⚠️ Capture impossible : pas sur le calendrier du championnat.")
        pymsgbox.alert(
            "Impossible de lancer la capture : ouvrez le calendrier du championnat.",
            title="Erreur"
        )
        return

    overlay.set_phase("Traitement des combats")
    total = traiter_tous_les_combats(logger, window)
    overlay.set_phase("En attente")
    pymsgbox.alert(
        f"Capture terminée. Combats traités : {total}",
        title="Fin de la capture"
    )


def boucle_principale(logger, window, overlay: Overlay):
    """Boucle d'attente principale pour les raccourcis clavier."""
    logger.info(
        "⌨️  Appuyez sur F1 pour l'aide, F3 pour lancer la capture, F9 pour le debug, ESC pour quitter."
    )
    keyboard.add_hotkey('f1', lambda: afficher_aide(logger))
    overlay.set_phase("En attente")
    keyboard.add_hotkey('f3', lambda: lancer_capture(logger, window, overlay))
    keyboard.add_hotkey('f8', lambda: overlay.toggle())
    keyboard.add_hotkey('f9', lambda: toggle_debug(logger))
    keyboard.wait('esc')
    logger.info("🚪 Touche ESC détectée : arrêt du programme.")
    overlay.stop()
