import os
import time
from typing import List, Dict

import keyboard as kb
import pyautogui
from PIL import Image
from pynput import mouse, keyboard as pynput_keyboard

from fonctions.overlay import Overlay


def capturer_templates(logger, window, overlay: Overlay, templates: List[Dict[str, str]]):
    """Lance la capture manuelle d'une liste de templates.

    Chaque élément de ``templates`` doit être un dict avec les clés ``path`` et
    ``description``. Les captures sont réalisées aux dimensions du premier
    fichier existant de la liste. L'utilisateur doit maintenir la touche CTRL et
    cliquer avec le bouton gauche pour prendre la capture à la position de la
    souris. Appuyer sur ESC interrompt la séquence.
    """
    if not templates:
        logger.warning("Aucun template à capturer")
        return

    # Détermination de la taille à utiliser
    width = height = None
    for tpl in templates:
        if os.path.exists(tpl["path"]):
            img = Image.open(tpl["path"])
            width, height = img.size
            break
    if width is None:
        width, height = 100, 100

    overlay.set_phase("Capture templates")
    index = 0
    stop_capture = False

    def on_click(x, y, button, pressed):
        nonlocal index, stop_capture
        if stop_capture:
            return False
        if not pressed:
            return
        if button != mouse.Button.left:
            return
        if not kb.is_pressed('ctrl'):
            return
        # Capture de la zone
        left = int(x - width / 2)
        top = int(y - height / 2)
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        os.makedirs(os.path.dirname(templates[index]["path"]), exist_ok=True)
        screenshot.save(templates[index]["path"])
        logger.info(f"Template sauvegardé : {templates[index]['path']}")
        index += 1
        if index >= len(templates):
            stop_capture = True
            return False
        overlay.set_action(templates[index]["description"])

    def on_press(key):
        nonlocal stop_capture
        if key == pynput_keyboard.Key.esc:
            stop_capture = True
            return False

    overlay.set_action(templates[index]["description"])
    with mouse.Listener(on_click=on_click) as listener, pynput_keyboard.Listener(on_press=on_press):
        while not stop_capture:
            time.sleep(0.1)

    overlay.set_phase("En attente")
    overlay.set_action("")
