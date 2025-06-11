import os
import shutil
from dotenv import load_dotenv
import pygetwindow as gw
import time
from configuration.config import WINDOW_WIDTH, WINDOW_HEIGHT, BLUESTACKS_WINDOW_TITLE, WINDOW_TIMEOUT_SECONDS


def lire_config_sous_forme_de_dictionnaire(path):
    config_dict = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                config_dict[k.strip()] = v.strip()
    return config_dict

def configurer_bluestacks(logger):
    load_dotenv()
    conf_path = os.getenv("BLUESTACKS_CONF_PATH")
    ref_path = os.path.join(os.path.dirname(__file__), "bluestacks_reference.conf")

    logger.debug(f"→ Fichier actuel : {conf_path}")
    logger.debug(f"→ Fichier de référence : {ref_path}")

    if not os.path.exists(conf_path):
        logger.error(f"❌ Fichier BlueStacks non trouvé : {conf_path}")
        return

    if not os.path.exists(ref_path):
        logger.error(f"❌ Fichier de référence manquant : {ref_path}")
        return

    # Lecture des fichiers sous forme de dictionnaire
    try:
        conf_dict = lire_config_sous_forme_de_dictionnaire(conf_path)
        ref_dict = lire_config_sous_forme_de_dictionnaire(ref_path)
    except Exception as e:
        logger.error(f"❌ Erreur lors de la lecture des fichiers : {e}")
        return

    if conf_dict == ref_dict:
        logger.info("✅ La configuration BlueStacks est déjà conforme.")
        return

    logger.warning("⚠️ La configuration BlueStacks est différente de la référence.")

    # Sauvegarde .bak
    backup_path = conf_path + ".bak"
    try:
        shutil.copyfile(conf_path, backup_path)
        logger.info(f"🛡 Sauvegarde de l'ancien fichier : {backup_path}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la sauvegarde : {e}")
        return

    # Remplacement
    try:
        shutil.copyfile(ref_path, conf_path)
        logger.info("✅ Configuration BlueStacks remplacée avec succès.")
    except Exception as e:
        logger.error(f"❌ Échec du remplacement de la configuration : {e}")

def verifier_fenetre_bluestacks(logger):
    """Vérifie que la fenêtre BlueStacks est visible et a les bonnes dimensions"""
    window = None
    for _ in range(WINDOW_TIMEOUT_SECONDS):
        windows = [w for w in gw.getWindowsWithTitle(BLUESTACKS_WINDOW_TITLE) if w.isVisible]
        if windows:
            window = windows[0]
            break
        time.sleep(1)

    if not window:
        logger.error("❌ Fenêtre BlueStacks non détectée ou non visible.")
        return None

    logger.debug(f"📐 Fenêtre détectée à {window.left}, {window.top}, taille {window.width}x{window.height}")

    if window.width != WINDOW_WIDTH or window.height != WINDOW_HEIGHT:
        logger.warning(f"⚠️ Taille inattendue : {window.width}x{window.height} (attendu : {WINDOW_WIDTH}x{WINDOW_HEIGHT})")
    else:
        logger.info("✅ Taille de la fenêtre BlueStacks conforme.")

    return window