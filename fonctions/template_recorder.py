import os
import time
import threading
from typing import List, Dict

import keyboard as kb
import pyautogui
from PIL import Image
from pynput import keyboard as pynput_keyboard, mouse as pynput_mouse
import tkinter as tk

from fonctions.overlay import Overlay


def capturer_templates(logger, window, overlay: Overlay, templates: List[Dict[str, str]]):
    """Lance la capture manuelle d'une liste de templates.

    Chaque élément de ``templates`` doit être un dict avec les clés ``path`` et
    ``description``. Les captures sont réalisées aux dimensions du premier
    fichier existant de la liste. L'utilisateur doit maintenir la touche CTRL et
    cliquer **droit** pour prendre la capture à la position de la souris.
    Appuyer sur ``p`` passe au template suivant sans capture. Appuyer sur
    ESC interrompt la séquence.
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

    overlay.set_phase("Capture templates (CTRL + clic droit)")
    index = 0
    stop_capture = False

    cursor_win = None
    cursor_canvas = None
    cursor_rect = None
    create_event = threading.Event()

    def create_cursor_window():
        nonlocal cursor_win, cursor_canvas, cursor_rect
        win = tk.Toplevel(overlay.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-transparentcolor", "magenta")
        win.configure(bg="magenta")
        win.geometry(f"{window.width}x{window.height}+{window.left}+{window.top}")

        canvas = tk.Canvas(win, width=window.width, height=window.height,
                           highlightthickness=0, bg="magenta")
        canvas.pack()
        rect = canvas.create_rectangle(0, 0, width, height,
                                       outline="red", width=2)
        canvas.itemconfigure(rect, state="hidden")

        cursor_win = win
        cursor_canvas = canvas
        cursor_rect = rect
        win.withdraw()
        create_event.set()

    overlay.root.after(0, create_cursor_window)
    create_event.wait()

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
        return "break"

    # La capture est déclenchée par un clic droit global lorsque CTRL est enfoncé
    def on_click(x, y, button, pressed):
        if (
            pressed
            and button == pynput_mouse.Button.right
            and kb.is_pressed("ctrl")
        ):
            capture_current()


    def on_press(key):
        nonlocal stop_capture, index
        if key == pynput_keyboard.Key.esc:
            stop_capture = True
            return False
        try:
            if key.char and key.char.lower() == 'p':
                logger.info("Template ignoré")
                index += 1
                if index >= len(templates):
                    stop_capture = True
                else:
                    overlay.set_action(templates[index]["description"])
        except AttributeError:
            pass

    def update_cursor():
        if stop_capture:
            cursor_win.withdraw()
            return
        if kb.is_pressed('ctrl'):
            x, y = pyautogui.position()
            left = int(x - width / 2)
            top = int(y - height / 2)
            # position relative to the BlueStacks window
            rel_x = left - window.left
            rel_y = top - window.top
            cursor_canvas.coords(cursor_rect,
                                rel_x,
                                rel_y,
                                rel_x + width,
                                rel_y + height)
            cursor_canvas.itemconfigure(cursor_rect, state="normal")
            cursor_win.geometry(f"{window.width}x{window.height}+{window.left}+{window.top}")
            cursor_win.deiconify()
        else:
            cursor_canvas.itemconfigure(cursor_rect, state="hidden")
            cursor_win.withdraw()
        overlay.root.after(30, update_cursor)

    overlay.set_action(templates[index]["description"])
    overlay.root.after(0, update_cursor)

    with pynput_keyboard.Listener(on_press=on_press) as key_listener, \
            pynput_mouse.Listener(on_click=on_click) as mouse_listener:
        while not stop_capture:
            time.sleep(0.1)

    overlay.set_phase("En attente")
    overlay.set_action("")
    overlay.root.after(0, cursor_win.destroy)
