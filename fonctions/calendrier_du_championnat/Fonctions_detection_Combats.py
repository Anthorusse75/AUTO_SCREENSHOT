import os
import time
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

def detecter_combats_simple(logger, window):
    """Version simplifiée et robuste de la détection de combats."""
    logger.debug("Détection simplifiée des combats")
    
    screenshot = pyautogui.screenshot(
        region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
    )
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    if len(screenshot_cv.shape) == 3:
        screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
    
    # Templates avec seuils adaptés
    templates_config = [
        ("victoire", "templates/calendrier_du_championnat/victoire_cdc.png", 0.75),
        ("egalite", "templates/calendrier_du_championnat/egalite_cdc.png", 0.70),
        ("defaite", "templates/calendrier_du_championnat/defaite_cdc.png", 0.65),
    ]
    
    combats = []
    positions_occupees = []
    
    for type_resultat, template_path, seuil in templates_config:
        if not os.path.exists(template_path):
            logger.warning(f"Template manquant: {template_path}")
            continue
            
        template = charger_image_cv2(template_path)
        if template is None:
            continue
        
        # Template matching global
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
        
        # Recherche de toutes les correspondances au-dessus du seuil
        locations = np.where(result >= seuil)
        
        for pt in zip(*locations[::-1]):
            # Éviter les détections trop proches (suppression non-max simple)
            trop_proche = False
            for pos_occupee in positions_occupees:
                distance = np.sqrt((pt[0] - pos_occupee[0])**2 + (pt[1] - pos_occupee[1])**2)
                if distance < 50:  # Distance minimum entre détections
                    trop_proche = True
                    break
            
            if trop_proche:
                continue
            
            positions_occupees.append(pt)
            
            # Score de cette détection
            score = result[pt[1], pt[0]]
            
            # Coordonnées absolues
            bbox = (
                window.left + pt[0],
                window.top + pt[1], 
                template.shape[1],
                template.shape[0],
            )
            
            center = (bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2)
            patch_hash = get_patch_hash_center(screenshot_cv, (pt[0] + template.shape[1]//2, pt[1] + template.shape[0]//2))
            
            combats.append({
                'id': len(combats) + 1,
                'coord': center,
                'type': type_resultat,
                'hash': patch_hash,
                'bbox': bbox,
                'score': score,
                'position_locale': pt
            })
            
            logger.debug(f"Combat {type_resultat} détecté à {pt}, score: {score:.3f}")
    
    # Tri par position (haut vers bas, gauche vers droite)
    combats.sort(key=lambda c: (c['position_locale'][1], c['position_locale'][0]))
    
    logger.info(f"Détection simplifiée: {len(combats)} combats trouvés")
    return combats
    """
    Nouvelle méthode de détection basée sur la grille fixe du calendrier.
    
    Le calendrier a 5 colonnes fixes. On définit les zones de chaque colonne
    et on cherche systématiquement dans chacune.
    """
    logger.debug("Début de la détection des combats (méthode grille)")
    
    # Définition des colonnes fixes (ajustables selon les vraies dimensions)
    # Ces coordonnées sont relatives à la fenêtre BlueStacks
    colonnes = [
        {"nom": "Lundi", "x_start": 78, "x_end": 310},      # Colonne 1
        {"nom": "Mardi", "x_start": 324, "x_end": 556},     # Colonne 2  
        {"nom": "Mercredi", "x_start": 570, "x_end": 802},  # Colonne 3
        {"nom": "Jeudi", "x_start": 816, "x_end": 1048},    # Colonne 4
        {"nom": "Vendredi", "x_start": 1062, "x_end": 1294} # Colonne 5
    ]
    
    # Zone verticale où chercher les combats (en excluant headers et footer)
    y_start = 120  # Après les en-têtes des jours
    y_end = 780    # Avant le bas de la fenêtre
    
    screenshot = pyautogui.screenshot(
        region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
    )
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    if len(screenshot_cv.shape) == 3:
        screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
    
    templates = {
        "victoire": os.path.join("templates", "calendrier_du_championnat", "victoire_cdc.png"),
        "egalite": os.path.join("templates", "calendrier_du_championnat", "egalite_cdc.png"),
        "defaite": os.path.join("templates", "calendrier_du_championnat", "defaite_cdc.png"),
    }
    
    combats = []
    seen_positions = []
    
    # Pour chaque type de résultat
    for type_resultat, template_path in templates.items():
        template = charger_image_cv2(template_path)
        if template is None:
            logger.warning(f"Template {type_resultat} introuvable : {template_path}")
            continue
            
        # Recherche dans chaque colonne
        for col_idx, colonne in enumerate(colonnes):
            # Zone de recherche dans cette colonne
            zone_x_start = max(0, colonne["x_start"])
            zone_x_end = min(screenshot_cv.shape[1], colonne["x_end"])
            zone_y_start = max(0, y_start)
            zone_y_end = min(screenshot_cv.shape[0], y_end)
            
            # Extraction de la zone de la colonne
            zone_colonne = screenshot_cv[zone_y_start:zone_y_end, zone_x_start:zone_x_end]
            
            if zone_colonne.size == 0:
                continue
                
            # Template matching dans cette zone
            result = cv2.matchTemplate(zone_colonne, template, cv2.TM_CCOEFF_NORMED)
            
            # Seuil adaptatif : commence bas et augmente selon le type
            if type_resultat == "victoire":
                threshold = 0.75  # Victoire souvent bien contrastée
            elif type_resultat == "egalite":
                threshold = 0.70  # Égalité parfois moins visible
            else:  # defaite
                threshold = 0.65  # Défaite peut être plus difficile à détecter
            
            locations = np.where(result >= threshold)
            
            for pt in zip(*locations[::-1]):
                # Conversion vers les coordonnées globales de l'écran
                global_x = zone_x_start + pt[0]
                global_y = zone_y_start + pt[1]
                
                # Éviter les doublons proches
                too_close = False
                for seen_pos in seen_positions:
                    if abs(global_x - seen_pos[0]) < 20 and abs(global_y - seen_pos[1]) < 20:
                        too_close = True
                        break
                        
                if too_close:
                    continue
                    
                seen_positions.append((global_x, global_y))
                
                # Coordonnées absolues à l'écran
                bbox = (
                    window.left + global_x,
                    window.top + global_y,
                    template.shape[1],
                    template.shape[0],
                )
                
                center = (bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2)
                patch_hash = get_patch_hash_center(screenshot_cv, (global_x + template.shape[1]//2, global_y + template.shape[0]//2))
                
                score = result[pt[1], pt[0]]
                
                combats.append({
                    'id': len(combats) + 1,
                    'coord': center,
                    'type': type_resultat,
                    'hash': patch_hash,
                    'bbox': bbox,
                    'colonne': col_idx,
                    'colonne_nom': colonne["nom"],
                    'score': score,
                    'position_locale': (global_x, global_y)
                })
                
                logger.debug(f"Combat {type_resultat} détecté dans {colonne['nom']} à ({global_x}, {global_y}), score: {score:.3f}")
    
    # Tri par colonne puis par position verticale
    combats.sort(key=lambda c: (c['colonne'], c['position_locale'][1]))
    
    logger.info(f"{len(combats)} combats détectés avec la méthode grille")
    return combats

def detecter_combats(logger, window):
    """
    Détecte tous les combats à l'écran.

    Les résultats 'Victoire' et 'Égalité' sont recherchés via leurs textes,
    tandis que les défaites sont détectées à partir des quatre bords du
    rectangle (def_haute, def_bas, def_gauche, def_droite).

    Retourne une liste de dicts contenant au minimum :
        - ``id``: identifiant séquentiel
        - ``coord``: centre du combat (x, y)
        - ``bbox``: rectangle complet (left, top, width, height)
        - ``type``: victoire/defaite/egalite
    """
    logger.debug("Début de la détection des combats")
    templates = {
        "victoire": os.path.join("templates", "calendrier_du_championnat", "victoire_cdc.png"),
        "egalite": os.path.join("templates", "calendrier_du_championnat", "egalite_cdc.png"),
        "defaite": os.path.join("templates", "calendrier_du_championnat", "defaite_cdc.png"),
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

        # Seuil plus permissif 
        threshold = max(0.7, COMBAT_MATCH_THRESHOLD * 0.85)
        loc = np.where(result >= threshold)

        for pt in zip(*loc[::-1]):
            # Évite les doublons proches (réduit la distance)
            if any(np.linalg.norm(np.array(pt) - np.array(s)) < 20 for s in seen):
                continue
            seen.append(pt)
            patch_hash = get_patch_hash(screenshot_cv, pt, template.shape)
            if patch_hash in [c['hash'] for c in combats]:
                continue  # déjà détecté dans cette passe
            bbox = (
                window.left + pt[0],
                window.top + pt[1],
                template.shape[1],
                template.shape[0],
            )
            
            score = result[pt[1], pt[0]]
            combats.append({
                'id': len(combats) + 1,
                'coord': (bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2),
                'type': type_resultat,
                'hash': patch_hash,
                'bbox': bbox,
                'score': score,
            })

    # Si pas assez de combats détectés avec les templates simples, on utilise la méthode rectangles pour les défaites
    defaites_simples = len([c for c in combats if c['type'] == 'defaite'])
    if defaites_simples == 0:
        logger.info("Aucune défaite détectée avec le template simple, tentative avec les rectangles...")
        rects_defaite = detecter_rectangles_defaite(logger, screenshot_cv)
        for rect in rects_defaite:
            center = (
                rect["x_gauche"] + (rect["x_droite"] - rect["x_gauche"]) // 2,
                rect["y_haute"] + (rect["y_basse"] - rect["y_haute"]) // 2,
            )
            if any(np.linalg.norm(np.array(center) - np.array(s)) < 20 for s in seen):
                continue
            seen.append(center)
            patch_hash = get_patch_hash_center(screenshot_cv, center)
            if patch_hash in [c['hash'] for c in combats]:
                continue
            bbox = (
                window.left + rect["x_gauche"],
                window.top + rect["y_haute"],
                rect["x_droite"] - rect["x_gauche"],
                rect["y_basse"] - rect["y_haute"],
            )
            combats.append({
                'id': len(combats) + 1,
                'coord': (bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2),
                'type': 'defaite',
                'hash': patch_hash,
                'bbox': bbox,
                'score': 0.8,  # Score estimé pour les rectangles
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

def grouper_combats_par_colonne(combats, tolerance=None):
    """Regroupe les combats par colonne en fonction de leur abscisse."""

    if not combats:
        return []

    positions = sorted(c["bbox"][0] for c in combats)
    if tolerance is None:
        diffs = [b - a for a, b in zip(positions, positions[1:])]
        if diffs:
            median = sorted(diffs)[len(diffs) // 2]
            tolerance = max(20, int(median * 0.5))
        else:
            tolerance = 80

    colonnes = []
    combats_tries = sorted(combats, key=lambda c: c["bbox"][0])
    for combat in combats_tries:
        placed = False
        for col in colonnes:
            if abs(combat["bbox"][0] - col["x"]) <= tolerance:
                col["combats"].append(combat)
                placed = True
                break
        if not placed:
            colonnes.append({"x": combat["bbox"][0], "combats": [combat]})

    for col in colonnes:
        col["combats"].sort(key=lambda c: c["bbox"][1])
    return colonnes

def debug_detection_combats_avance(logger, window, overlay, pause=3.0):
    """Affiche un debug avancé avec comparaison des deux méthodes de détection."""
    logger.info("Démarrage du debug avancé de détection des combats")
    
    # Test des deux méthodes
    overlay.set_phase("Debug avancé")
    overlay.set_action("Méthode normale...")
    
    combats_normal = detecter_combats(logger, window)
    logger.info(f"Méthode normale: {len(combats_normal)} combats")
    
    overlay.set_action("Méthode simple...")
    combats_grille = detecter_combats_simple(logger, window)
    logger.info(f"Méthode simple: {len(combats_grille)} combats")
    
    # Affichage détaillé
    tous_combats = []
    
    # Ajout des combats de la méthode normale
    for combat in combats_normal:
        combat['methode'] = 'normale'
        tous_combats.append(combat)
    
    # Ajout des combats de la méthode simple
    for combat in combats_grille:
        combat['methode'] = 'simple'
        tous_combats.append(combat)
    
    if not tous_combats:
        overlay.set_phase("En attente")
        overlay.set_action("Aucun combat détecté")
        logger.warning("Aucun combat détecté avec aucune des deux méthodes!")
        return
    
    # Fonction d'affichage séquentiel
    def afficher_combat(idx=0):
        if idx >= len(tous_combats):
            overlay.set_phase("En attente")
            overlay.set_action("Debug terminé")
            return
        
        combat = tous_combats[idx]
        methode = combat.get('methode', 'inconnue')
        type_combat = combat.get('type', 'inconnu')
        score = combat.get('score', 0)
        colonne_info = ""
        
        if 'colonne_nom' in combat:
            colonne_info = f" - {combat['colonne_nom']}"
        
        overlay.set_action(f"{idx+1}/{len(tous_combats)}: {methode} - {type_combat}{colonne_info} (score: {score:.2f})")
        
        bbox = combat.get('bbox')
        if bbox:
            # Couleur selon la méthode
            color = "green" if methode == 'simple' else "red"
            overlay.highlight_rectangle(bbox, duration=int(pause * 1000), color=color)
        
        # Next combat après la pause
        overlay.root.after(int(pause * 1000), lambda: afficher_combat(idx + 1))
    
    # Démarrer l'affichage
    overlay.root.after(0, lambda: afficher_combat())

def debug_detection_combats(logger, window, overlay, pause=2.0):
    """Affiche chaque combat détecté via un cadre overlay pour debug."""
    logger.info("Démarrage du debug de détection des combats")
    
    # Utilise la nouvelle méthode simple par défaut
    combats = detecter_combats_simple(logger, window)
    logger.info(f"{len(combats)} combats trouvés pour le debug")
    
    if not combats:
        overlay.set_phase("En attente")
        overlay.set_action("Aucun combat")
        overlay.root.after(int(pause * 1000), lambda: overlay.set_action(""))
        return

    colonnes = grouper_combats_par_colonne(combats)
    overlay.set_phase("Debug combats")

    def afficher(col=0, idx=0):
        if col >= len(colonnes):
            overlay.set_phase("En attente")
            overlay.set_action("")
            return

        courant = colonnes[col]["combats"]
        if idx >= len(courant):
            overlay.root.after(int(pause * 1000), lambda: afficher(col + 1, 0))
            return

        combat = courant[idx]
        score = combat.get('score', 0)
        colonne_nom = combat.get('colonne_nom', f'Col {col+1}')
        overlay.set_action(
            f"{colonne_nom} - {combat['type']} (score: {score:.2f})"
        )
        overlay.highlight_rectangle(combat.get("bbox"), duration=int(pause * 1000))
        overlay.root.after(int(pause * 1000), lambda: afficher(col, idx + 1))

    overlay.root.after(0, lambda: afficher())

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
    time.sleep(0.5)  # Court délai pour la fermeture de la fenêtre
    return True

# --- 4. Fonction principale d'automatisation ---
def traiter_tous_les_combats(logger, window):
    """Traite tous les combats détectés et renvoie le nombre de combats réalisés."""
    logger.debug("Démarrage du traitement de tous les combats")
    deja_vus = set()
    total_traites = 0
    while True:
        # Utilise la nouvelle méthode simple pour une meilleure détection
        combats = detecter_combats_simple(logger, window)
        # Filtrer ceux déjà cliqués (par leur hash)
        combats_a_traiter = [c for c in combats if c['hash'] not in deja_vus]
        if not combats_a_traiter:
            logger.info("✅ Plus aucun combat à traiter, automation terminée.")
            break

        for combat in combats_a_traiter:
            cliquer_sur_coord(logger, combat['coord'])
            pyautogui.sleep(2.0)  # Laisse le temps à la page de charger

            # Vérifie si on est bien sur la page JGG
            page = detecter_page_actuelle(logger, window)
            if page and page.get("page") == "journal_de_guerre_de_guildes":
                cliquer_croix_sortie_JGG(logger, window)
                pyautogui.sleep(2.0)
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
