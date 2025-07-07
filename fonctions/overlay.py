import tkinter as tk

class Overlay:
    """Petite fenêtre superposée indiquant l'état courant."""

    def __init__(self, window, width=360, height=60):
        self.window = window
        self.width = width
        self.height = height
        self.visible = True

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)

        self.phase_var = tk.StringVar(value="Initialisation")
        self.action_var = tk.StringVar(value="")

        frame = tk.Frame(self.root, bg="black")
        frame.pack(fill="both", expand=True)
        wrap = self.width - 10
        tk.Label(frame,
                 textvariable=self.phase_var,
                 fg="white",
                 bg="black",
                 font=("Arial", 12, "bold"),
                 anchor="w",
                 justify="left",
                 wraplength=wrap).pack(fill="x", padx=5, pady=(4, 0))
        tk.Label(frame,
                 textvariable=self.action_var,
                 fg="white",
                 bg="black",
                 font=("Arial", 10),
                 anchor="w",
                 justify="left",
                 wraplength=wrap).pack(fill="x", padx=5, pady=(0, 4))

        # Ajuste la hauteur pour s'adapter au contenu si nécessaire
        self.root.update_idletasks()
        self.height = max(self.height, frame.winfo_height())

        self.update_position()

    def start(self):
        """Démarre la boucle Tk de l'overlay."""
        self.root.mainloop()

    def stop(self):
        """Arrête la boucle Tk en toute sécurité."""
        self.root.after(0, self.root.quit)

    def update_position(self):
        if self.window:
            x = self.window.left + self.window.width - self.width
            y = self.window.top
            self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        self.root.after(500, self.update_position)

    def set_phase(self, text: str):
        self.root.after(0, self.phase_var.set, text)

    def set_action(self, text: str):
        self.root.after(0, self.action_var.set, text)

    def hide(self):
        if self.visible:
            self.root.after(0, self.root.withdraw)
            self.visible = False

    def show(self):
        if not self.visible:
            self.root.after(0, self.root.deiconify)
            self.visible = True

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def highlight_rectangle(self, bbox, duration=2000, color="lime", width=3):
        """Affiche un rectangle temporaire sur la fenêtre BlueStacks."""

        def _show():
            win = tk.Toplevel(self.root)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            win.attributes("-transparentcolor", "magenta")
            win.configure(bg="magenta")
            canvas = tk.Canvas(
                win,
                width=self.window.width,
                height=self.window.height,
                highlightthickness=0,
                bg="magenta",
            )
            canvas.pack()
            left = bbox[0] - self.window.left
            top = bbox[1] - self.window.top
            canvas.create_rectangle(
                left,
                top,
                left + bbox[2],
                top + bbox[3],
                outline=color,
                width=width,
            )
            win.geometry(
                f"{self.window.width}x{self.window.height}+{self.window.left}+{self.window.top}"
            )
            win.after(duration, win.destroy)

        self.root.after(0, _show)
