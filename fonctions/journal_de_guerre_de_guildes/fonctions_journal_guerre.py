#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyser_journaux_guerre_guildes.py

Fonctions pour analyser et parcourir les journaux de guerre de guildes
dans BlueStacks/Summoners War. La logique a été revue pour garantir un
scroll 100 % fiable via gestes tactiles simulés (swipe vertical), car
la molette Windows est souvent ignorée par BlueStacks.

Principales améliorations
-------------------------
- Focus fenêtre : restore + activate pour éviter le « scroll dans le vide ».
- Swipe vertical : dx = 0, distance 600 px, durée 0.8 s (naturel pour Android).
- Option fallback ADB (HD-Adb.exe) si PyAutoGUI reste inopérant.
- Logs détaillés (Niveau DEBUG) pour chaque test de template et swipe.
- Détection de fin de scroll : template + fallback luminosité.
"""

from __future__ import annotations

import os
import time
import subprocess
from typing import List, Tuple, Optional

import cv2
import numpy as np
import pyautogui

# --- repérage de la bordure dorée ------------------------------------------
GOLD_MIN   = 180          # seuil gris-clair ≈ bordure dorée
SCAN_RANGE = 140          # on ne remonte / descend jamais de > 140 px

# --------------------------------------------------------------------------- #
#  Tout en haut du fichier – juste après les imports existants
# --------------------------------------------------------------------------- #
import shutil                 #  <-- déjà peut-être importé plus bas ? sinon ajoute
### DEBUG SCREENSHOTS ##############################################
DIR_LOG_ROOT = "LOG_SCREENSHOTS"
DIR_LOG = DIR_LOG_ROOT

import datetime, tempfile

def _init_log_dir(logger):
    """
    Prépare un dossier dédié pour la session de debug des captures.

    Pour éviter les erreurs d'accès sous Windows (répertoire encore ouvert),
    on crée simplement un sous-dossier horodaté à chaque exécution au lieu de
    supprimer l'ancien.
    """
    global DIR_LOG
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    DIR_LOG = os.path.join(DIR_LOG_ROOT, ts)
    try:
        os.makedirs(DIR_LOG, exist_ok=True)
        logger.debug(f"[DEBUG] Dossier {DIR_LOG}/ prêt")
    except Exception as e:
        logger.error(f"Impossible de créer {DIR_LOG}: {e}")

def _save_debug(bgr_img, rects, idx):
    """
    Sauvegarde un screenshot annoté dans LOG_SCREENSHOTS/.
    rects = [(x1, y1, x2, y2, score_float), ...]
    """
    img = bgr_img.copy()
    for x1, y1, x2, y2, score in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 2)
        label = f"{int(score*100):02d}%"
        cv2.rectangle(img, (x1, y1 - 22), (x1 + 38, y1), (0, 0, 0), -1)
        cv2.putText(img, label, (x1 + 2, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1,
                    cv2.LINE_AA)
    cv2.imwrite(f"{DIR_LOG}/{idx:03d}.png", img)
####################################################################

# --------------------------------------------------------------------------- #
#  Imports internes (vos propres modules / constantes)                        #
# --------------------------------------------------------------------------- #
from configuration.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    TEMPLATES_PAGES_DIR,     # <– laissé pour compatibilité si utilisé ailleurs
    TAB_MATCH_THRESHOLD,
    LIMIT_MATCH_THRESHOLD,
    PAGE_MATCH_THRESHOLD,
)
from fonctions.detection_page import (
    charger_image_cv2,
    detecter_onglet_actif,   # peut servir hors de ce module
    detecter_limites_scroll, # idem
)
from configuration.fenetre_utils import cliquer_coordonnees

# --------------------------------------------------------------------------- #
#  Gestes « scroll » (swipe vertical) et géométrie du tableau                #
# --------------------------------------------------------------------------- #
SWIPE_DISTANCE = 780               # px
SWIPE_DURATION = 0.55              # s

PANEL_X1 = 250                # bord gauche « brun »
PANEL_X2 = 1340               # juste avant la colonne barre dorée
ROW_X1, ROW_X2 = PANEL_X1, PANEL_X2
ROW_UP, ROW_DOWN = 80, 65     # englobe la ligne « Position : n »
ROW_W, ROW_H = ROW_X2 - ROW_X1, ROW_UP + ROW_DOWN

SWIPE_X = (ROW_X1 + ROW_X2) // 2   # trajectoire pile au centre du tableau

def find_row_bounds(gray: np.ndarray, cx: int, cy: int) -> Tuple[int, int]:
    """Remonte puis descend depuis ``cy`` pour détecter la bordure dorée.

    Si aucune zone claire n'est trouvée dans la portée ``SCAN_RANGE``
    on retombe sur les marges ``ROW_UP``/``ROW_DOWN``.
    """
    y_top = cy
    for dy in range(1, SCAN_RANGE + 1):
        y = cy - dy
        if y < 0:
            break
        if gray[y, cx] > GOLD_MIN:
            y_top = y
            break

    y_bot = cy
    H = gray.shape[0]
    for dy in range(1, SCAN_RANGE + 1):
        y = cy + dy
        if y >= H:
            break
        if gray[y, cx] > GOLD_MIN:
            y_bot = y
            break

    if y_bot <= y_top:
        # Fallback : pas de bordure détectée
        y_top = max(cy - ROW_UP, 0)
        y_bot = min(cy + ROW_DOWN, H)

    return y_top, y_bot

# --------------------------------------------------------------------------- #
#  Helpers fenêtre et gestes                                                 #
# --------------------------------------------------------------------------- #

def focus_fenetre_bluestacks(window) -> None:
    """
    Donne *réellement* le focus à la fenêtre BlueStacks.

    - Si la fenêtre est minimisée, on la restaure avant d'appeler .activate().
    - On met un petit sleep pour laisser le temps à Windows de réagir.
    """
    try:
        import pygetwindow as gw

        win = gw.getWindowsWithTitle(window.title)[0]
        if win.isMinimized:
            win.restore()
        win.activate()
        time.sleep(0.3)
    except Exception as e:
        # On loggue en stdout car le logger n'est pas forcément dispo ici
        print(f"[WARN] Impossible de focus la fenêtre BlueStacks : {e}")
        time.sleep(0.3)


def swipe_vertical(x: int, y_start: int, y_end: int,
                   duration: float = SWIPE_DURATION,
                   logger=None, label: str = "swipe") -> None:
    """
    Swipe Android fiable :
    1. micro-nudge (-2,-2) → réveille l’input
    2. mouseDown
    3. dragRel(dx=10, dy, duration)
    """
    dy = y_end - y_start
    if logger:
        logger.debug(f"🖱️ {label} start=({x},{y_start}) dy={dy} dur={duration:.1f}s")

    pyautogui.moveTo(x - 2, y_start - 2, _pause=False)   # nudge
    pyautogui.moveTo(x, y_start, _pause=False)
    pyautogui.mouseDown()
    pyautogui.dragRel(10, dy, duration=duration, button='left', _pause=False)
    pyautogui.mouseUp()


def swipe_adb(
    x: int,
    y_start: int,
    y_end: int,
    duration_ms: int = 500,
    logger=None,
) -> None:
    """
    Fallback : swipe via ADB interne BlueStacks (HD-Adb.exe).
    Très fiable si PyAutoGUI échoue (capture VNC directement par Android).

    duration_ms : durée du swipe côté Android.
    """
    cmd = [
        "HD-Adb.exe",
        "shell",
        "input",
        "swipe",
        str(x),
        str(y_start),
        str(x),
        str(y_end),
        str(duration_ms),
    ]
    if logger:
        logger.debug("⏯️  Exécution commande ADB : " + " ".join(cmd))
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# --------------------------------------------------------------------------- #
#  Détection onglets et limites de scroll                                     #
# --------------------------------------------------------------------------- #

def detecter_onglet_journal_attaque(logger, screenshot_cv) -> bool:
    """Retourne True si le tab *Journal d'attaque* est actif."""
    template_path = "templates/journal_de_guerre_de_guildes/onglets/journal_d_attaque.png"
    if not os.path.exists(template_path):
        logger.warning(f"Template onglet attaque introuvable : {template_path}")
        return False

    template = charger_image_cv2(template_path)
    if template is None:
        logger.error(f"Impossible de charger le template : {template_path}")
        return False

    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    logger.debug(f"Score onglet attaque : {max_val:.3f}")
    return max_val >= TAB_MATCH_THRESHOLD


def detecter_onglet_journal_defense(logger, screenshot_cv) -> bool:
    """Retourne True si le tab *Journal de défense* est actif."""
    template_path = "templates/journal_de_guerre_de_guildes/onglets/journal_de_defense.png"
    if not os.path.exists(template_path):
        logger.warning(f"Template onglet défense introuvable : {template_path}")
        return False

    template = charger_image_cv2(template_path)
    if template is None:
        logger.error(f"Impossible de charger le template : {template_path}")
        return False

    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    logger.debug(f"Score onglet défense : {max_val:.3f}")
    return max_val >= TAB_MATCH_THRESHOLD


def detecter_bouton_journal_defense(logger, screenshot_cv) -> Optional[Tuple[int, int]]:
    """
    Détecte le bouton *Journal de défense* et renvoie son centre (x, y).
    Retourne None si score < TAB_MATCH_THRESHOLD.
    """
    template_path = "templates/journal_de_guerre_de_guildes/onglets/bouton_journal_defense.png"
    if not os.path.exists(template_path):
        logger.warning(f"Template bouton défense introuvable : {template_path}")
        return None

    template = charger_image_cv2(template_path)
    if template is None:
        logger.error(f"Impossible de charger le template : {template_path}")
        return None

    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    logger.debug(f"Score bouton défense : {max_val:.3f}")

    if max_val >= TAB_MATCH_THRESHOLD:
        h, w = template.shape[:2]
        return (max_loc[0] + w // 2, max_loc[1] + h // 2)
    return None


# --------------------------------------------------------------------------- #
#  Détection des informations de combat sur l'écran courant                   #
# --------------------------------------------------------------------------- #

def detecter_informations_combat(
    logger,
    screenshot_cv,
    exclusions: Optional[List[Tuple[int, int]]] = None,
) -> List[Tuple[int, int]]:
    """
    Renvoie toutes les positions (x, y) des icônes *informations_combat*
    visibles à l'écran, en filtrant les doublons et les coords déjà connues.
    """
    template_path = "templates/journal_de_guerre_de_guildes/informations_combat.png"
    if not os.path.exists(template_path):
        logger.warning(f"Template informations combat introuvable : {template_path}")
        return []

    template = charger_image_cv2(template_path)
    if template is None:
        logger.error(f"Impossible de charger le template : {template_path}")
        return []

    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= PAGE_MATCH_THRESHOLD)

    if exclusions is None:
        exclusions = []

    positions: List[Tuple[int, int]] = []
    h, w = template.shape[:2]

    for pt in zip(*locations[::-1]):  # (y, x) -> (x, y)
        cx, cy = pt[0] + w // 2, pt[1] + h // 2

        # anti-doublon : déjà connu ?
        if any(np.hypot(cx - ex, cy - ey) < 50 for ex, ey in exclusions):
            continue
        if any(np.hypot(cx - px, cy - py) < 50 for px, py in positions):
            continue

        positions.append((cx, cy))

    logger.debug(
        f"Détecté {len(positions)} info(s) combat "
        f"(exclu={len(exclusions)}) sur cette capture"
    )
    return positions


# --------------------------------------------------------------------------- #
#  Détection de fin de scroll (haut / bas)                                    #
# --------------------------------------------------------------------------- #

def _detecter_fin_scroll(
    logger,
    screenshot_cv,
    template_file: str,
    zone: str,  # "haut" ou "bas" (pour logs)
) -> bool:
    """
    Renvoie True si la limite de scroll (haut ou bas) est détectée.

    - D'abord on tente la détection par template.
    - Sinon fallback : luminosité sur 100 px en haut ou bas d'écran.
    """
    if not os.path.exists(template_file):
        logger.debug(f"Template limite {zone} absent, fallback luminosité")
        slice_ = (
            screenshot_cv[:100, :] if zone == "haut" else screenshot_cv[-100:, :]
        )
        return np.mean(slice_) > 200

    template = charger_image_cv2(template_file)
    if template is None:
        return False

    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    logger.debug(f"Limite {zone} score : {max_val:.3f}")
    return max_val >= 0.92        # 0.92 ≃ visuellement identique


def detecter_fin_scroll_haut(logger, screenshot_cv) -> bool:
    """True si l'on est en haut de la liste."""
    return _detecter_fin_scroll(
        logger,
        screenshot_cv,
        "templates/journal_de_guerre_de_guildes/limites/haut_scroll.png",
        zone="haut",
    )


def detecter_fin_scroll_bas(logger, screenshot_cv) -> bool:
    """True si l'on est en bas de la liste."""
    return _detecter_fin_scroll(
        logger,
        screenshot_cv,
        "templates/journal_de_guerre_de_guildes/limites/bas_scroll.png",
        zone="bas",
    )

def scroll_tactile_vers_haut(
    logger,
    window,
    overlay,
    distance: int = SWIPE_DISTANCE,
    duree: float = SWIPE_DURATION,
    repetitions: int = 1,
) -> None:
    """
    Swipe vertical du bas vers le haut pour faire défiler la liste vers le haut.
    """
    x = window.left + (ROW_X1 + ROW_X2) // 2
    y_start = window.top + WINDOW_HEIGHT // 2 + distance // 2

    for _ in range(repetitions):
        focus_fenetre_bluestacks(window)
        overlay.set_action("Swipe haut")
        logger.info(f"🖱️ Swipe haut ({distance}px) depuis ({x},{y_start})")
        swipe_vertical(
            x,
            y_start,
            y_start - distance,
            duration=duree,
            logger=logger,
            label="haut",
        )
        time.sleep(0.9)  # laisser l'inertie se dissiper


def scroll_tactile_vers_bas(
    logger,
    window,
    overlay,
    distance: int = SWIPE_DISTANCE,
    duree: float = SWIPE_DURATION,
    repetitions: int = 1,
) -> None:
    """
    Swipe vertical du haut vers le bas pour faire défiler la liste vers le bas.
    """
    x = window.left + (ROW_X1 + ROW_X2) // 2
    y_start = window.top + WINDOW_HEIGHT // 2 - distance // 2

    for _ in range(repetitions):
        focus_fenetre_bluestacks(window)
        overlay.set_action("Swipe bas")
        logger.info(f"🖱️ Swipe bas ({distance}px) depuis ({x},{y_start})")
        swipe_vertical(
            x,
            y_start,
            y_start + distance,
            duration=duree,
            logger=logger,
            label="bas",
        )
        time.sleep(0.9)



# --------------------------------------------------------------------------- #
#  Parcours complet d'un journal (attaque ou défense)                         #
# --------------------------------------------------------------------------- #

def parcourir_journal_complet(
    logger,
    window,
    overlay,
    type_journal: str = "attaque",
) -> List[Tuple[int, int]]:
    """
    Parcourt tout le journal (attaque ou défense) pour collecter les combats.

    Retourne la liste de *toutes* les positions (x, y) détectées.
    """
    logger.info(f"🔍 Parcours du journal {type_journal}")
    overlay.set_phase(f"Journal {type_journal}")

    toutes_positions: List[Tuple[int, int]] = []

    # 1. Vérification de l'onglet ouvert
    screenshot = pyautogui.screenshot(
        region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
    )
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    onglet_ok = (
        detecter_onglet_journal_attaque
        if type_journal == "attaque"
        else detecter_onglet_journal_defense
    )
    if not onglet_ok(logger, screenshot_cv):
        logger.error("❌ Mauvais onglet ouvert – abandon")
        return []

    ### DEBUG SCREENSHOTS ###
    debug_idx = 0  # compteur de fichiers
    _save_debug(np.array(screenshot)[:, :, ::-1], [], debug_idx)
    debug_idx += 1
    ################################

    # 2. Remonter tout en haut
    for _ in range(20):
        screenshot = pyautogui.screenshot(
            region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        if detecter_fin_scroll_haut(logger, screenshot_cv):
            logger.info("✅ Haut atteint")
            break
        scroll_tactile_vers_haut(logger, window, overlay)

        ### DEBUG SCREENSHOTS ###
        _save_debug(np.array(screenshot)[:, :, ::-1], [], debug_idx)
        debug_idx += 1
        ################################

    # 3. Descente progressive + collecte combats
    iteration = 0
    while True:
        iteration += 1
        screenshot = pyautogui.screenshot(
            region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

        # 3.a Détection combats
        nouvelles = detecter_informations_combat(logger, screenshot_cv, toutes_positions)
        if nouvelles:
            logger.info(f"✨ +{len(nouvelles)} combat(s) détecté(s)")
            toutes_positions.extend(nouvelles)

            # Highlight visuel pour debug
            # juste après toutes_positions.extend(nouvelles)
            blocs = []
            for px, py in nouvelles:              # <- plus « nouvelles » (validées)
                y1, y2 = find_row_bounds(screenshot_cv, px, py)
                right = max(px - 55, ROW_X1 + 1)
                if y2 <= y1 or right <= ROW_X1:
                    continue  # zone invalide
                # score réel de corrélation
                crop = screenshot_cv[y1:y2, ROW_X1:right]
                _, score, _, _ = cv2.minMaxLoc(
                    cv2.matchTemplate(crop, crop, cv2.TM_CCOEFF_NORMED))
                blocs.append((ROW_X1, y1, right, y2, score))
                time.sleep(0.15)
        else:
            logger.debug("Aucun nouveau combat sur cette vue")

        ### DEBUG SCREENSHOTS ###
        # on encadre chaque bloc complet du combat nouvellement détecté
        blocs = []
        for px, py in nouvelles:
            y1, y2 = find_row_bounds(screenshot_cv, px, py)
            right = max(px - 55, ROW_X1 + 1)
            if y2 <= y1 or right <= ROW_X1:
                continue
            blocs.append((ROW_X1 + 2, y1, right, y2, 1.0))  # score fictif 1.0
        _save_debug(np.array(screenshot)[:, :, ::-1], blocs, debug_idx)
        debug_idx += 1
        ################################

        # 3.b Scroll vers le bas
        scroll_tactile_vers_bas(logger, window, overlay)

        screenshot = pyautogui.screenshot(
            region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        if detecter_fin_scroll_bas(logger, screenshot_cv):
            logger.info("✅ Bas atteint")
            break

        ### DEBUG SCREENSHOTS ###
        _save_debug(np.array(screenshot)[:, :, ::-1], [], debug_idx)
        debug_idx += 1
        ################################

        # Sécurité
        if iteration > 50:
            logger.warning("⚠️ Plus de 50 itérations – arrêt d'urgence")
            break

    logger.info(
        f"▶️ Fin parcours {type_journal} – total : {len(toutes_positions)} combats"
    )
    return toutes_positions


# --------------------------------------------------------------------------- #
#  Analyse complète (remplace ancienne touche F7)                             #
# --------------------------------------------------------------------------- #

def analyser_journaux_guerre_guildes(logger, window, overlay):
    """
    Lance une analyse complète : journal d'attaque PUIS journal de défense.

    Résultat : dict { 'attaque': [...], 'defense': [...], 'total': int }
    """
    logger.info("🚀 Analyse des journaux de guerre de guildes")
    overlay.set_phase("Analyse journaux")

    ### DEBUG SCREENSHOTS ###
    _init_log_dir(logger)
    ################################

    # Vérification onglet attaque initial
    screenshot = pyautogui.screenshot(
        region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
    )
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    if not detecter_onglet_journal_attaque(logger, screenshot_cv):
        logger.error("❌ Onglet attaque NON ouvert – stop")
        overlay.set_phase("Erreur onglet")
        return

    # 1) Analyse journal d'attaque
    positions_attaque = parcourir_journal_complet(logger, window, overlay, "attaque")
    logger.info(f"📊 Attaque : {len(positions_attaque)} combats")

    # 2) Bascule vers journal de défense
    overlay.set_action("Changement onglet défense")
    screenshot = pyautogui.screenshot(
        region=(window.left, window.top, WINDOW_WIDTH, WINDOW_HEIGHT)
    )
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    bouton = detecter_bouton_journal_defense(logger, screenshot_cv)
    if bouton:
        cliquer_coordonnees(logger, window, bouton[0], bouton[1])
        time.sleep(2)  # laisser l'UI changer d'onglet
    else:
        logger.error("❌ Bouton défense introuvable – analyse incomplète")
        return

    # 3) Analyse journal de défense
    positions_defense = parcourir_journal_complet(logger, window, overlay, "defense")
    logger.info(f"📊 Défense : {len(positions_defense)} combats")

    # 4) Résumé final
    total = len(positions_attaque) + len(positions_defense)
    logger.info(
        f"🎯 Analyse terminée – Total {total} "
        f"(Atk {len(positions_attaque)}, Def {len(positions_defense)})"
    )
    overlay.set_phase("Analyse terminée")

    return {
        "attaque": positions_attaque,
        "defense": positions_defense,
        "total": total,
    }
