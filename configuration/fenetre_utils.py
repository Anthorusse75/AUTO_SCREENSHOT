import time
import pygetwindow as gw
import pyautogui

from configuration.config import (
    BLUESTACKS_WINDOW_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_TIMEOUT_SECONDS
)

def initialiser_fenetre_bluestacks(logger):
    """Vérifie l'existence, la taille et la position de la fenêtre BlueStacks"""

    window = trouver_fenetre(logger)
    if not window:
        logger.error("❌ Impossible de démarrer : fenêtre BlueStacks non trouvée.")
        return None

    # On tente de restaurer si la fenêtre est minimisée (cas tricky Windows)
    window = forcer_reaffichage_si_minimise(window, logger)
    if not window or (hasattr(window, "left") and window.left == -32000):
        logger.critical("❌ Impossible de restaurer la fenêtre BlueStacks (elle est minimisée). Ouvre-la manuellement et relance le script.")
        return None

    try:
        window.activate()
        logger.debug("🪟 Fenêtre BlueStacks activée (focus demandé).")
    except Exception as e:
        logger.warning(f"⚠️ Impossible de forcer le focus : {e}")

    # 🔧 Redimensionner d'abord
    redimensionner_si_necessaire(window, logger)

    # 📍 Repositionner après le redimensionnement
    repositionner_fenetre_si_necessaire(window, logger)

    # 🧾 Vérifier dimensions (log informatif)
    verifier_dimensions(window, logger)

    logger.info("🎯 Fenêtre BlueStacks initialisée avec succès.")
    return window


def forcer_reaffichage_si_minimise(window, logger):
    # pygetwindow ne fournit pas de méthode isMinimized, on check par la position classique (-32000,-32000)
    if window.left == -32000 and window.top == -32000:
        logger.warning("🛑 Fenêtre BlueStacks minimisée ! Impossible de la manipuler tant qu’elle est dans la barre des tâches.")
        # Essaie de restaurer
        try:
            window.restore()
            logger.info("🪟 Fenêtre restaurée depuis l’état minimisé.")
            import time
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"❌ Impossible de restaurer la fenêtre minimisée : {e}")
            return False
        # Après .restore(), il faut retrouver l’objet window mis à jour
        # (pygetwindow ne met pas à jour automatiquement les coords)
        import pygetwindow as gw
        new_windows = [w for w in gw.getWindowsWithTitle(window.title) if w.left != -32000]
        if new_windows:
            window = new_windows[0]
        else:
            logger.error("❌ Impossible de retrouver la fenêtre après restauration.")
            return False
    return window

def redimensionner_si_necessaire(window, logger):
    # Toujours restaurer avant de manipuler la fenêtre
    try:
        window.restore()
        logger.info("🪟 Fenêtre restaurée (démaximisée) avant redimensionnement.")
        time.sleep(0.7)  # On attend plus longtemps
    except Exception as e:
        logger.warning(f"⚠️ Impossible de restaurer la fenêtre (peut-être déjà restaurée) : {e}")

    # On essaie plusieurs fois de resize, car BlueStacks parfois re-maximise ou ignore la première demande
    for tentative in range(3):
        if window.width == WINDOW_WIDTH and window.height == WINDOW_HEIGHT:
            logger.debug("📏 Dimensions correctes après restauration.")
            return True
        try:
            window.resizeTo(WINDOW_WIDTH, WINDOW_HEIGHT)
            logger.info(f"✅ Fenêtre redimensionnée (tentative {tentative + 1}).")
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"❌ Impossible de redimensionner la fenêtre : {e}")
        # Refresh window info (parfois il faut relire l’objet)
        import pygetwindow as gw
        windows = [w for w in gw.getWindowsWithTitle(window.title) if w.visible]
        if windows:
            window = windows[0]
    if window.width != WINDOW_WIDTH or window.height != WINDOW_HEIGHT:
        logger.warning(f"⚠️ Dimensions inattendues après plusieurs tentatives : {window.width}x{window.height} (attendu : {WINDOW_WIDTH}x{WINDOW_HEIGHT})")
        return False
    logger.debug("📏 Dimensions correctes après plusieurs tentatives.")
    return True

def trouver_fenetre(logger):
    """Retourne la fenêtre BlueStacks si elle est visible et existante"""
    logger.debug("🔍 Recherche de la fenêtre BlueStacks...")
    window = None
    for _ in range(WINDOW_TIMEOUT_SECONDS):
        windows = [w for w in gw.getWindowsWithTitle(BLUESTACKS_WINDOW_TITLE) if w.visible]
        if windows:
            window = windows[0]
            break
        time.sleep(1)

    if not window:
        logger.error("❌ Fenêtre BlueStacks introuvable ou non visible.")
    else:
        logger.info(f"✅ Fenêtre trouvée à ({window.left},{window.top}) taille {window.width}x{window.height}")

    return window


def verifier_dimensions(window, logger):
    """Vérifie que la fenêtre a la bonne taille"""
    if window.width != WINDOW_WIDTH or window.height != WINDOW_HEIGHT:
        logger.warning(f"⚠️ Dimensions inattendues : {window.width}x{window.height} (attendu : {WINDOW_WIDTH}x{WINDOW_HEIGHT})")
        return False
    logger.info("📏 Dimensions de la fenêtre conformes.")
    return True


def ajuster_coordonnees(window, x_local, y_local):
    """Convertit des coordonnées relatives à BlueStacks en coordonnées écran absolues"""
    return window.left + x_local, window.top + y_local


def cliquer_coordonnees(logger, window, x_local, y_local):
    """Clique sur une coordonnée relative à BlueStacks"""
    x, y = ajuster_coordonnees(window, x_local, y_local)
    logger.debug(f"🖱 Clique à {x}, {y}")
    pyautogui.click(x, y)

def repositionner_fenetre_si_necessaire(window, logger):
    """Replace la fenêtre si elle est partiellement ou totalement hors écran"""

    screen_width, screen_height = pyautogui.size()
    margin = 5  # marge de tolérance

    x, y = window.left, window.top
    w, h = window.width, window.height

    # Fenêtre totalement hors écran
    if (x + margin >= screen_width or y + margin >= screen_height
            or x + w <= 0 or y + h <= 0):
        logger.warning("🧭 Fenêtre totalement hors écran : repositionnement forcé.")
        window.moveTo(0, 0)
        return True

    # Fenêtre partiellement hors écran (tolérance faible)
    if x < 0 or y < 0 or (x + w) > screen_width or (y + h) > screen_height:
        logger.warning("🧭 Fenêtre partiellement hors écran : repositionnement.")
        window.moveTo(0, 0)
        return True

    logger.debug("✅ Position de la fenêtre correcte.")
    return False