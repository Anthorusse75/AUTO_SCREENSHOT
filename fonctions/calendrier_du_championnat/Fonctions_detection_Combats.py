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
    COMBAT_RECT_MATCH_THRESHOLD,
)
from fonctions.detection_page import detecter_page_actuelle, charger_image_cv2

def detecter_combats(logger, window):
    """
    Détecte tous les combats à l'écran.

    Les résultats 'Victoire' et 'Égalité' sont recherchés via leurs textes,
    tandis que les défaites sont détectées à partir des quatre bords du
    rectangle (def_haute, def_bas, def_gauche, def_droite).

    Retourne une liste de dicts : { 'id': int, 'coord': (x, y), 'type': str, 'clicked': False }
    """
    logger.debug("Début de la détection des combats")
    templates = {
        "victoire": os.path.join("templates", "calendrier_du_championnat", "victoire_cdc.png"),
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

    # Détection des rectangles de défaite via les bords
    rects_defaite = detecter_rectangles_defaite(logger, screenshot_cv)
    for rect in rects_defaite:
        center = (
            rect["x_gauche"] + (rect["x_droite"] - rect["x_gauche"]) // 2,
            rect["y_haute"] + (rect["y_basse"] - rect["y_haute"]) // 2,
        )
        if any(np.linalg.norm(np.array(center) - np.array(s)) < 30 for s in seen):
            continue
        seen.append(center)
        patch_hash = get_patch_hash_center(screenshot_cv, center)
        if patch_hash in [c['hash'] for c in combats]:
            continue
        combats.append({
            'id': len(combats) + 1,
            'coord': (window.left + center[0], window.top + center[1]),
            'type': 'defaite',
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

def get_patch_hash_center(screenshot_cv, center, patch_size=(60, 20)):
    """Calcule un hash d'une zone autour du centre fourni."""
    x_c, y_c = center
    w, h = patch_size
    x1 = max(int(x_c - w // 2), 0)
    y1 = max(int(y_c - h // 2), 0)
    x2 = min(x1 + w, screenshot_cv.shape[1])
    y2 = min(y1 + h, screenshot_cv.shape[0])
    patch = screenshot_cv[y1:y2, x1:x2]
    return hashlib.md5(patch.tobytes()).hexdigest()

def detecter_rectangles_defaite(logger, screenshot_cv):
    """Détecte les rectangles de résultat 'Défaite' à partir des 4 bords."""
    dossier = os.path.join("templates", "calendrier_du_championnat", "defaite")
    fichiers = {
        "haut": "def_haute.png",
        "bas": "def_bas.png",
        "gauche": "def_gauche.png",
        "droite": "def_droite.png",
    }

    matches = {}
    tailles = {}
    for nom, fichier in fichiers.items():
        chemin = os.path.join(dossier, fichier)
        template = charger_image_cv2(chemin)
        if template is None:
            logger.error(f"Template {chemin} introuvable")
            return []
        res = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= COMBAT_RECT_MATCH_THRESHOLD)
        matches[nom] = list(zip(*loc[::-1]))
        tailles[nom] = (template.shape[1], template.shape[0])

    rectangles = []
    tol = 5
    for (xg, yg) in matches.get("gauche", []):
        for (xd, yd) in matches.get("droite", []):
            if abs(yd - yg) <= tol and xd > xg:
                for (xt, yt) in matches.get("haut", []):
                    if abs(yt - yg) <= tol and abs(xt - xg) <= tol:
                        for (xb, yb) in matches.get("bas", []):
                            if abs(xb - xg) <= tol and yb > yt:
                                rect = {
                                    "x_gauche": xg + tailles["gauche"][0],
                                    "x_droite": xd,
                                    "y_haute": yt + tailles["haut"][1],
                                    "y_basse": yb,
                                }
                                rectangles.append(rect)
                                break
                        break
                break
    logger.info(f"{len(rectangles)} rectangles de défaite détectés")
    return rectangles

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
    """Traite tous les combats détectés et renvoie le nombre de combats réalisés."""
    logger.debug("Démarrage du traitement de tous les combats")
    deja_vus = set()
    total_traites = 0
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
                    total_traites += 1
                else:
                    logger.warning("Pas revenu au calendrier, arrêt.")
                    return total_traites
            else:
                logger.warning("Pas sur la page JGG après clic, arrêt.")
                return total_traites

    logger.info("Nombre total de combats traités : %s", total_traites)
    return total_traites

# --- 5. Fonction de suivi des combats déjà cliqués (optionnel si tu veux persister l'état) ---
# Ici, on garde tout en mémoire, mais tu peux sauvegarder la liste combats dans un fichier si besoin.
