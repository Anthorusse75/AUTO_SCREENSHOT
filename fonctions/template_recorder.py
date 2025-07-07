import os
import time
from typing import List, Dict

import keyboard as kb
import pyautogui
from PIL import Image
from pynput import keyboard as pynput_keyboard
import tkinter as tk

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

    # Petite fenêtre affichant le cadre de capture lorsque CTRL est maintenu
    def create_cursor_window():
        win = tk.Toplevel(overlay.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-transparentcolor", "magenta")
        win.configure(bg="magenta")
        canvas = tk.Canvas(win, width=width, height=height, highlightthickness=0, bg="magenta")
        canvas.pack()
        canvas.create_rectangle(0, 0, width - 1, height - 1, outline="red", width=2)
        win.withdraw()
        return win

    cursor_win = create_cursor_window()

    def capture_current(_event=None):
        nonlocal index, stop_capture
        if stop_capture or not kb.is_pressed('ctrl'):
            return "break"
        x, y = pyautogui.position()
        left = int(x - width / 2)
        top = int(y - height / 2)
        cursor_win.withdraw()
        overlay.root.update_idletasks()
        time.sleep(0.05)
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        os.makedirs(os.path.dirname(templates[index]["path"]), exist_ok=True)
        screenshot.save(templates[index]["path"])
        logger.info(f"Template sauvegardé : {templates[index]['path']}")
        index += 1
        if index >= len(templates):
            stop_capture = True
        else:
            overlay.set_action(templates[index]["description"])
        cursor_win.deiconify()
        return "break"

    cursor_win.bind("<Button-1>", capture_current)

    def on_press(key):
        nonlocal stop_capture
        if key == pynput_keyboard.Key.esc:
            stop_capture = True
            return False

    def update_cursor():
        if stop_capture:
            cursor_win.withdraw()
            return
        if kb.is_pressed('ctrl'):
            x, y = pyautogui.position()
            left = int(x - width / 2)
            top = int(y - height / 2)
            cursor_win.geometry(f"{width}x{height}+{left}+{top}")
            cursor_win.deiconify()
        else:
            cursor_win.withdraw()
        overlay.root.after(30, update_cursor)

    overlay.set_action(templates[index]["description"])
    overlay.root.after(0, update_cursor)

    with pynput_keyboard.Listener(on_press=on_press):
        while not stop_capture:
            time.sleep(0.1)

    overlay.set_phase("En attente")
    overlay.set_action("")
    overlay.root.after(0, cursor_win.destroy)
