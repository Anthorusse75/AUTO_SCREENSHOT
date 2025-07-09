#!/usr/bin/env python3
"""
Fonctions pour analyser et parcourir les journaux de guerre de guildes.
"""
import os
import time
import cv2
import numpy as np
import pyautogui

from configuration.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    TEMPLATES_PAGES_DIR,
    TAB_MATCH_THRESHOLD,
    LIMIT_MATCH_THRESHOLD,
    PAGE_MATCH_THRESHOLD
)
from fonctions.detection_page import charger_image_cv2, detecter_onglet_actif, detecter_limites_scroll
from configuration.fenetre_utils import cliquer_coordonnees


def detecter_onglet_journal_attaque(logger, screenshot_cv):
    """Détecte si on est sur l'onglet 'Journal d'attaque'."""
    template_path = "templates/journal_de_guerre_de_guildes/onglets/journal_d_attaque.png"
    
    if not os.path.exists(template_path):
        logger.warning(f"Template journal d'attaque non trouvé : {template_path}")
        return False
    
    template = charger_image_cv2(template_path)
    if template is None:
        logger.error(f"Impossible de charger le template : {template_path}")
        return False
    
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    
    logger.debug(f"Score détection onglet attaque : {max_val:.3f}")
    return max_val >= TAB_MATCH_THRESHOLD


def detecter_onglet_journal_defense(logger, screenshot_cv):
    """Détecte si on est sur l'onglet 'Journal de défense'."""
    template_path = "templates/journal_de_guerre_de_guildes/onglets/journal_de_defense.png"
    
    if not os.path.exists(template_path):
        logger.warning(f"Template journal de défense non trouvé : {template_path}")
        return False
    
    template = charger_image_cv2(template_path)
    if template is None:
        logger.error(f"Impossible de charger le template : {template_path}")
        return False
    
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    
    logger.debug(f"Score détection onglet défense : {max_val:.3f}")
    return max_val >= TAB_MATCH_THRESHOLD


def detecter_bouton_journal_defense(logger, screenshot_cv):
    """Détecte et retourne la position du bouton pour basculer vers journal de défense."""
    template_path = "templates/journal_de_guerre_de_guildes/onglets/bouton_journal_defense.png"
    
    if not os.path.exists(template_path):
        logger.warning(f"Template bouton défense non trouvé : {template_path}")
        return None
    
    template = charger_image_cv2(template_path)
    if template is None:
        logger.error(f"Impossible de charger le template : {template_path}")
        return None
    
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= TAB_MATCH_THRESHOLD:
        # Calcul du centre du bouton
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        logger.debug(f"Bouton journal défense trouvé à ({center_x}, {center_y}) avec score {max_val:.3f}")
        return (center_x, center_y)
    
    logger.debug(f"Bouton journal défense non trouvé (score : {max_val:.3f})")
    return None


def detecter_informations_combat(logger, screenshot_cv, exclusions=None):
    """
    Détecte tous les éléments 'informations_combat.png' dans la capture d'écran.
    
    Args:
        logger: Logger pour les messages
        screenshot_cv: Image de la capture d'écran en OpenCV
        exclusions: Liste des positions déjà détectées à exclure (format: [(x, y), ...])
    
    Returns:
        Liste des positions trouvées [(x, y), ...]
    """
    template_path = "templates/journal_de_guerre_de_guildes/informations_combat.png"
    
    if not os.path.exists(template_path):
        logger.warning(f"Template informations combat non trouvé : {template_path}")
        return []
    
    template = charger_image_cv2(template_path)
    if template is None:
        logger.error(f"Impossible de charger le template : {template_path}")
        return []
    
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= PAGE_MATCH_THRESHOLD)
    
    if exclusions is None:
        exclusions = []
    
    positions = []
    h, w = template.shape[:2]
    
    for pt in zip(*locations[::-1]):  # Conversion (y, x) -> (x, y)
        center_x = pt[0] + w // 2
        center_y = pt[1] + h // 2
        
        # Vérifier si cette position est trop proche d'une exclusion
        est_exclue = False
        for excl_x, excl_y in exclusions:
            distance = np.sqrt((center_x - excl_x)**2 + (center_y - excl_y)**2)
            if distance < 50:  # Seuil de 50 pixels pour éviter les doublons
                est_exclue = True
                break
        
        if not est_exclue:
            # Vérifier si cette position est trop proche d'une déjà trouvée
            est_doublon = False
            for pos_x, pos_y in positions:
                distance = np.sqrt((center_x - pos_x)**2 + (center_y - pos_y)**2)
                if distance < 50:
                    est_doublon = True
                    break
            
            if not est_doublon:
                positions.append((center_x, center_y))
    
    logger.debug(f"Détecté {len(positions)} informations de combat (exclusions: {len(exclusions)})")
    return positions


def detecter_fin_scroll_haut(logger, screenshot_cv):
    """Détecte si on est arrivé en haut du scroll."""
    template_path = "templates/journal_de_guerre_de_guildes/limites/haut_scroll.png"
    
    if not os.path.exists(template_path):
        logger.debug("Template haut de scroll non trouvé, utilisation de méthode alternative")
        # Méthode alternative : vérifier s'il y a du contenu très en haut
        hauteur_verification = 100
        zone_haut = screenshot_cv[:hauteur_verification, :]
        return np.mean(zone_haut) > 200  # Zone claire = on est en haut
    
    template = charger_image_cv2(template_path)
    if template is None:
        return False
    
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    
    return max_val >= LIMIT_MATCH_THRESHOLD


def detecter_fin_scroll_bas(logger, screenshot_cv):
    """Détecte si on est arrivé en bas du scroll."""
    template_path = "templates/journal_de_guerre_de_guildes/limites/bas_scroll.png"
    
    if not os.path.exists(template_path):
        logger.debug("Template bas de scroll non trouvé, utilisation de méthode alternative")
        # Méthode alternative : vérifier s'il y a du contenu très en bas
        hauteur_verification = 100
        zone_bas = screenshot_cv[-hauteur_verification:, :]
        return np.mean(zone_bas) > 200  # Zone claire = on est en bas
    
    template = charger_image_cv2(template_path)
    if template is None:
        return False
    
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    
    return max_val >= LIMIT_MATCH_THRESHOLD


def scroller_vers_haut(logger, window, overlay, zone_scroll_center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2)):
    """
    Scrolle doucement vers le haut jusqu'à atteindre le début.
    
    Args:
        zone_scroll_center: Centre de la zone de scroll (x, y)
    """
    logger.info("📜 Scroll vers le haut en cours...")
    overlay.set_action("Scroll vers le haut")
    
    scroll_attempts = 0
    max_attempts = 20
    
    while scroll_attempts < max_attempts:
        # Prendre une capture pour vérifier où on en est
        screenshot = pyautogui.screenshot(region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT))
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        
        # Vérifier si on est arrivé en haut
        if detecter_fin_scroll_haut(logger, screenshot_cv):
            logger.info("✅ Arrivé en haut du scroll")
            break
        
        # Scroll doux vers le haut
        x_scroll, y_scroll = zone_scroll_center
        x_global, y_global = window.left + x_scroll, window.top + y_scroll
        
        pyautogui.scroll(3, x_global, y_global)  # Scroll doux de 3 unités
        time.sleep(0.3)  # Pause pour éviter l'inertie
        scroll_attempts += 1
    
    if scroll_attempts >= max_attempts:
        logger.warning("⚠️ Nombre maximum de tentatives de scroll atteint")
    
    time.sleep(0.5)  # Stabilisation finale


def scroller_vers_bas(logger, window, overlay, zone_scroll_center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2)):
    """
    Scrolle doucement vers le bas pour voir de nouveaux éléments.
    
    Returns:
        bool: True si le scroll a été effectué, False si on était déjà en bas
    """
    # Prendre une capture avant le scroll
    screenshot_avant = pyautogui.screenshot(region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT))
    screenshot_cv_avant = cv2.cvtColor(np.array(screenshot_avant), cv2.COLOR_RGB2GRAY)
    
    # Vérifier si on est déjà en bas
    if detecter_fin_scroll_bas(logger, screenshot_cv_avant):
        logger.info("✅ Déjà en bas du scroll")
        return False
    
    # Effectuer le scroll
    x_scroll, y_scroll = zone_scroll_center
    x_global, y_global = window.left + x_scroll, window.top + y_scroll
    
    pyautogui.scroll(-3, x_global, y_global)  # Scroll doux de 3 unités vers le bas
    time.sleep(0.5)  # Attendre la stabilisation
    
    overlay.set_action("Scroll vers le bas")
    logger.debug("📜 Scroll vers le bas effectué")
    return True


def parcourir_journal_complet(logger, window, overlay, type_journal="attaque"):
    """
    Parcourt complètement un journal (attaque ou défense) et détecte tous les combats.
    
    Args:
        type_journal: "attaque" ou "defense"
    
    Returns:
        Liste de toutes les positions des informations de combat détectées
    """
    logger.info(f"🔍 Début du parcours du journal de {type_journal}")
    overlay.set_phase(f"Journal {type_journal}")
    
    toutes_positions = []
    
    # 1. Vérifier qu'on est sur le bon onglet
    screenshot = pyautogui.screenshot(region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT))
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    
    if type_journal == "attaque":
        if not detecter_onglet_journal_attaque(logger, screenshot_cv):
            logger.error("❌ Pas sur l'onglet journal d'attaque")
            return []
    else:
        if not detecter_onglet_journal_defense(logger, screenshot_cv):
            logger.error("❌ Pas sur l'onglet journal de défense")
            return []
    
    # 2. Scroller tout en haut
    scroller_vers_haut(logger, window, overlay)
    
    # 3. Parcourir de haut en bas
    scroll_possible = True
    iteration = 0
    
    while scroll_possible:
        iteration += 1
        logger.debug(f"📄 Itération {iteration} du parcours")
        
        # Prendre une nouvelle capture
        screenshot = pyautogui.screenshot(region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT))
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        
        # Détecter les nouveaux combats (en excluant ceux déjà trouvés)
        nouvelles_positions = detecter_informations_combat(logger, screenshot_cv, toutes_positions)
        
        if nouvelles_positions:
            logger.info(f"✨ Trouvé {len(nouvelles_positions)} nouveau(x) combat(s)")
            toutes_positions.extend(nouvelles_positions)
            
            # Encadrer chaque nouveau combat pour le debug
            for pos_x, pos_y in nouvelles_positions:
                overlay.highlight_rectangle(
                    (window.left + pos_x - 25, window.top + pos_y - 15, 50, 30),
                    duration=1000,
                    color="green"
                )
                time.sleep(0.2)  # Petit délai entre chaque encadrement
        else:
            logger.debug("Aucun nouveau combat détecté")
        
        # Essayer de scroller vers le bas
        scroll_possible = scroller_vers_bas(logger, window, overlay)
        
        # Sécurité : limite le nombre d'itérations
        if iteration > 50:
            logger.warning("⚠️ Nombre maximum d'itérations atteint")
            break
    
    logger.info(f"✅ Parcours terminé - Total: {len(toutes_positions)} combats détectés")
    return toutes_positions


def analyser_journaux_guerre_guildes(logger, window, overlay):
    """
    Fonction principale pour analyser complètement les journaux de guerre de guildes.
    Cette fonction remplace l'ancienne fonction F7.
    """
    logger.info("🚀 Début de l'analyse complète des journaux de guerre de guildes")
    overlay.set_phase("Analyse journaux")
    
    # Vérifier qu'on est bien sur la page journal de guerre de guildes
    screenshot = pyautogui.screenshot(region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT))
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    
    # Étape 0: Vérifier qu'on est sur journal d'attaque
    if not detecter_onglet_journal_attaque(logger, screenshot_cv):
        logger.error("❌ Pas sur l'onglet journal d'attaque. Veuillez d'abord y naviguer.")
        overlay.set_phase("Erreur - Mauvais onglet")
        return
    
    # Étapes 1-6: Parcourir le journal d'attaque
    positions_attaque = parcourir_journal_complet(logger, window, overlay, "attaque")
    logger.info(f"📊 Journal d'attaque: {len(positions_attaque)} combats détectés")
    
    # Étape 7: Basculer vers journal de défense
    logger.info("🔄 Basculement vers journal de défense")
    overlay.set_action("Changement d'onglet")
    
    # Prendre une nouvelle capture pour détecter le bouton
    screenshot = pyautogui.screenshot(region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT))
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    
    bouton_defense = detecter_bouton_journal_defense(logger, screenshot_cv)
    if bouton_defense:
        cliquer_coordonnees(logger, window, bouton_defense[0], bouton_defense[1])
        time.sleep(2)  # Attendre le changement d'onglet
        logger.info("✅ Clic sur journal de défense effectué")
    else:
        logger.error("❌ Impossible de trouver le bouton journal de défense")
        return
    
    # Étape 8: Parcourir le journal de défense
    positions_defense = parcourir_journal_complet(logger, window, overlay, "defense")
    logger.info(f"📊 Journal de défense: {len(positions_defense)} combats détectés")
    
    # Résumé final
    total_combats = len(positions_attaque) + len(positions_defense)
    logger.info(f"🎯 Analyse terminée - Total: {total_combats} combats (Attaque: {len(positions_attaque)}, Défense: {len(positions_defense)})")
    overlay.set_phase("Analyse terminée")
    
    return {
        "attaque": positions_attaque,
        "defense": positions_defense,
        "total": total_combats
    }
