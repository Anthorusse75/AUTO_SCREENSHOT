import os
import cv2
import numpy as np
import pyautogui
import hashlib

from configuration.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    TEMPLATES_PAGES_DIR,
    COMBAT_MATCH_THRESHOLD,
)
from fonctions.detection_page import detecter_page_actuelle, charger_image_cv2

def detecter_combats(logger, window):
    """
    Détecte tous les combats à l'écran en cherchant les textes 'Victoire', 'Défaite', 'Égalité'.
    Retourne une liste de dicts : { 'id': int, 'coord': (x, y), 'type': str, 'clicked': False }
    """
    templates = {
        "victoire": os.path.join("templates", "calendrier_du_championnat", "victoire_cdc.png"),
        "defaite": os.path.join("templates", "calendrier_du_championnat", "defaite_cdc.png"),
        "egalite": os.path.join("templates", "calendrier_du_championnat", "egalite_cdc.png"),
    }
    screenshot = pyautogui.screenshot(
        region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
    )
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    if len(screenshot_cv.shape) == 3:
        screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)

    combats = []
    seen = []

    for type_resultat, template_path in templates.items():
        template = charger_image_cv2(template_path)
        if template is None:
            logger.error(f"Template {type_resultat} introuvable : {template_path}")
            continue

        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        logger.info(f"{type_resultat}: max_val={max_val:.3f} at {max_loc}")

        loc = np.where(result >= COMBAT_MATCH_THRESHOLD)

        for pt in zip(*loc[::-1]):
            # Évite les doublons proches (non-max suppression simplifiée)
            if any(np.linalg.norm(np.array(pt) - np.array(s)) < 30 for s in seen):
                continue
            seen.append(pt)
            patch_hash = get_patch_hash(screenshot_cv, pt, template.shape)
            if patch_hash in [c['hash'] for c in combats]:
                continue  # déjà détecté dans cette passe
            combats.append({
                'id': len(combats) + 1,
                'coord': (window.left + pt[0] + template.shape[1] // 2, window.top + pt[1] + template.shape[0] // 2),
                'type': type_resultat,
                'hash': patch_hash,
            })
    logger.info(f"{len(combats)} combats détectés à l'écran (victoire/défaite/égalité).")
    return combats

def get_patch_hash(screenshot_cv, pt, template_shape, patch_size=(60, 20)):
    # Centre du template détecté
    x_c = pt[0] + template_shape[1] // 2
    y_c = pt[1] + template_shape[0] // 2
    w, h = patch_size
    x1 = max(x_c - w // 2, 0)
    y1 = max(y_c - h // 2, 0)
    x2 = min(x1 + w, screenshot_cv.shape[1])
    y2 = min(y1 + h, screenshot_cv.shape[0])
    patch = screenshot_cv[y1:y2, x1:x2]
    # Hash du patch
    return hashlib.md5(patch.tobytes()).hexdigest()

# --- 2. Fonction de clic générique ---
def cliquer_sur_coord(logger, coord):
    x, y = coord
    logger.info(f"Clique sur le combat à {x},{y}")
    pyautogui.click(x, y)

# --- 3. Fonction pour cliquer sur la croix de sortie JGG ---
def cliquer_croix_sortie_JGG(logger, window):
    template_path = os.path.join(
        TEMPLATES_PAGES_DIR, "..", "journal_de_guerre_de_guildes", "croix_sortie_JGG.png"
    )
    template = charger_image_cv2(template_path)
    screenshot = pyautogui.screenshot(
        region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
    )
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    if len(screenshot_cv.shape) == 3:
        screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val < 0.8:
        logger.warning("Croix de sortie JGG non trouvée.")
        return False
    x = window.left + max_loc[0] + template.shape[1] // 2
    y = window.top + max_loc[1] + template.shape[0] // 2
    logger.info(f"Clique sur la croix de sortie JGG à {x},{y}")
    pyautogui.click(x, y)
    return True

# --- 4. Fonction principale d'automatisation ---
def traiter_tous_les_combats(logger, window):
    deja_vus = set()
    while True:
        combats = detecter_combats(logger, window)
        # Filtrer ceux déjà cliqués (par leur hash)
        combats_a_traiter = [c for c in combats if c['hash'] not in deja_vus]
        if not combats_a_traiter:
            logger.info("✅ Plus aucun combat à traiter, automation terminée.")
            break

        for combat in combats_a_traiter:
            cliquer_sur_coord(logger, combat['coord'])
            pyautogui.sleep(1.5)  # Laisse le temps à la page de charger

            # Vérifie si on est bien sur la page JGG
            page = detecter_page_actuelle(logger, window)
            if page and page.get("page") == "journal_de_guerre_de_guildes":
                cliquer_croix_sortie_JGG(logger, window)
                pyautogui.sleep(1.5)
                # Vérifie retour au calendrier
                page = detecter_page_actuelle(logger, window)
                if page and page.get("page") == "calendrier_du_championnat":
                    logger.info("Retour au calendrier, on continue.")
                    deja_vus.add(combat['hash'])
                else:
                    logger.warning("Pas revenu au calendrier, arrêt.")
                    return
            else:
                logger.warning("Pas sur la page JGG après clic, arrêt.")
                return

# --- 5. Fonction de suivi des combats déjà cliqués (optionnel si tu veux persister l'état) ---
# Ici, on garde tout en mémoire, mais tu peux sauvegarder la liste combats dans un fichier si besoin.