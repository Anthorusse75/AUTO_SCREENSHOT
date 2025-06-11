import os
import json
import cv2
import numpy as np
import pyautogui
from configuration.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    TEMPLATES_PAGES_DIR, PAGES_STRUCTURE_PATH,
    PAGE_MATCH_THRESHOLD, TAB_MATCH_THRESHOLD, LIMIT_MATCH_THRESHOLD
)

def charger_image_cv2(path):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
    # Conversion systématique en niveaux de gris pour uniformiser
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img

def comparer_images(img1, img2):
    # Vérifie que les deux images existent et ont le même format
    if img1 is None or img2 is None:
        return 0.0
    if img1.shape[0] < img2.shape[0] or img1.shape[1] < img2.shape[1]:
        return 0.0
    result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return max_val

def detecter_onglet_actif(logger, screenshot_cv, dossier_onglets):
    if not os.path.isdir(dossier_onglets):
        logger.warning(f"❌ Dossier onglets introuvable : {dossier_onglets}")
        return None
    scores = {}
    for fichier in os.listdir(dossier_onglets):
        if not fichier.lower().endswith(".png"):
            continue
        chemin_template = os.path.join(dossier_onglets, fichier)
        template = charger_image_cv2(chemin_template)
        if template is None:
            logger.warning(f"⚠️ Erreur de chargement du template : {chemin_template}")
            continue
        score = comparer_images(screenshot_cv, template)
        scores[fichier] = score
    if not scores:
        logger.warning("⚠️ Aucun onglet analysé.")
        return None
    meilleur_onglet, score = max(scores.items(), key=lambda x: x[1])
    if score >= TAB_MATCH_THRESHOLD:
        nom_onglet = os.path.splitext(meilleur_onglet)[0]
        logger.info(f"📄 Onglet actif détecté : {nom_onglet} (score {score:.2f})")
        return nom_onglet
    else:
        logger.warning("❌ Aucun onglet ne correspond avec certitude.")
        return None

def detecter_limites_scroll(logger, screenshot_cv, dossier_limites):
    """
    Cherche les positions des 4 limites (haute, basse, gauche, droite).
    Retourne un dict {x_gauche, x_droite, y_haute, y_basse} ou None si problème.
    """
    limites_fichiers = {
        "haute": "haute.png",
        "basse": "basse.png",
        "gauche": "gauche.png",
        "droite": "droite.png",
    }
    positions = {}
    for direction, fichier in limites_fichiers.items():
        chemin = os.path.join(dossier_limites, fichier)
        tpl = charger_image_cv2(chemin)
        if tpl is None:
            logger.warning(f"⚠️ Impossible de charger la limite {direction}: {chemin}")
            return None
        res = cv2.matchTemplate(screenshot_cv, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val < LIMIT_MATCH_THRESHOLD:
            logger.warning(f"⚠️ Limite {direction} non trouvée (score {max_val:.2f})")
            return None
        positions[direction] = (max_loc, tpl.shape)
    # Rectangle : gauche = x droite, droite = x gauche, haute = y basse, basse = y haute
    rect = {
        "x_gauche": positions["gauche"][0][0] + positions["gauche"][1][1],
        "x_droite": positions["droite"][0][0],
        "y_haute": positions["haute"][0][1] + positions["haute"][1][0],
        "y_basse": positions["basse"][0][1],
    }
    logger.info(f"🔲 Rectangle de scroll détecté : {rect}")
    return rect

def detecter_page_actuelle(logger, window):
    if not window:
        logger.error("❌ Impossible de détecter la page : fenêtre BlueStacks non trouvée.")
        return None
    # Capture écran BlueStacks (fenêtre passée en paramètre)
    screenshot = pyautogui.screenshot(region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT))
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    if len(screenshot_cv.shape) == 3:
        screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
    try:
        with open(PAGES_STRUCTURE_PATH, "r", encoding="utf-8") as f:
            structure = json.load(f)
    except Exception as e:
        logger.critical(f"❌ Impossible de charger la structure des pages : {e}")
        return None
    scores_pages = {}
    for page_name, config in structure.items():
        template_file = config.get("template")
        if not template_file:
            continue
        chemin_template = os.path.join(TEMPLATES_PAGES_DIR, template_file)
        template = charger_image_cv2(chemin_template)
        if template is None:
            logger.warning(f"⚠️ Erreur de chargement : {chemin_template}")
            continue
        score = comparer_images(screenshot_cv, template)
        scores_pages[page_name] = (score, config)
    if not scores_pages:
        logger.warning("❌ Aucun template analysé.")
        return None
    page_detectee, (score, config) = max(scores_pages.items(), key=lambda x: x[1][0])
    if score < PAGE_MATCH_THRESHOLD:
        logger.warning(f"❌ Aucune correspondance fiable (score max : {score:.2f})")
        return None
    logger.info(f"🧭 Page détectée : {page_detectee} (score {score:.2f})")
    # Vérifie les onglets si présents
    onglet_actif = None
    limites_scroll = None
    if "onglets" in config:
        dossier_onglets = os.path.join(TEMPLATES_PAGES_DIR, config["onglets"]["dossier"])
        onglet_actif = detecter_onglet_actif(logger, screenshot_cv, dossier_onglets)
    # Vérifie les limites si la page le demande
    if "limites" in config:
        dossier_limites = os.path.join(TEMPLATES_PAGES_DIR, config["limites"]["dossier"])
        limites_scroll = detecter_limites_scroll(logger, screenshot_cv, dossier_limites)
    return {
        "page": page_detectee,
        "onglet": onglet_actif,
        "limites": limites_scroll,
    }
