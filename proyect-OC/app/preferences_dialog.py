import tkinter as tk
from tkinter import ttk


class PreferencesDialog(tk.Toplevel):
    def __init__(self, parent, prefs_manager, on_apply_callback):
        super().__init__(parent)
        self.title("Preferencias")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.prefs = prefs_manager
        self.on_apply_callback = on_apply_callback

        self.font_size_var = tk.IntVar(value=self.prefs.get("editor", "font_size"))
        self.font_family_var = tk.StringVar(value=self.prefs.get("editor", "font_family"))
        self.theme_mode_var = tk.StringVar(value=self.prefs.get("theme", "mode"))
        self.zoom_percent_var = tk.IntVar(value=self.prefs.get("ui", "zoom_percent"))

        self._build_ui()
        self._center(parent)

        self.bind("<Escape>", lambda _e: self.destroy())

    def _build_ui(self):
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        editor_frame = ttk.LabelFrame(container, text="Editor", padding=10)
        editor_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(editor_frame, text="Tipo de fuente:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        font_combo = ttk.Combobox(
            editor_frame,
            textvariable=self.font_family_var,
            values=["Courier", "Consolas", "Lucida Console", "Courier New"],
            state="readonly",
            width=18,
        )
        font_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 6))

        ttk.Label(editor_frame, text="Tamaño de fuente:").grid(row=1, column=0, sticky="w")
        size_spin = ttk.Spinbox(
            editor_frame,
            from_=8,
            to=24,
            increment=1,
            textvariable=self.font_size_var,
            width=7,
        )
        size_spin.grid(row=1, column=1, sticky="w", padx=(10, 0))

        theme_frame = ttk.LabelFrame(container, text="Tema", padding=10)
        theme_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(theme_frame, text="Modo:").grid(row=0, column=0, sticky="w")
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_mode_var,
            values=["light", "dark"],
            state="readonly",
            width=18,
        )
        theme_combo.grid(row=0, column=1, sticky="w", padx=(10, 0))

        ui_frame = ttk.LabelFrame(container, text="Interfaz", padding=10)
        ui_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(ui_frame, text="Zoom global (%):").grid(row=0, column=0, sticky="w")
        zoom_spin = ttk.Spinbox(
            ui_frame,
            from_=80,
            to=200,
            increment=5,
            textvariable=self.zoom_percent_var,
            width=7,
        )
        zoom_spin.grid(row=0, column=1, sticky="w", padx=(10, 0))

        button_row = ttk.Frame(container)
        button_row.pack(fill="x")

        ttk.Button(button_row, text="Guardar", command=self._save).pack(side="right")
        ttk.Button(button_row, text="Cancelar", command=self.destroy).pack(side="right", padx=(0, 8))

    def _save(self):
        self.prefs.set("editor", "font_size", self.font_size_var.get())
        self.prefs.set("editor", "font_family", self.font_family_var.get())
        self.prefs.set("theme", "mode", self.theme_mode_var.get())
        self.prefs.set("ui", "zoom_percent", self.zoom_percent_var.get())
        self.prefs.save()

        if callable(self.on_apply_callback):
            self.on_apply_callback()

        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        x = px + max((pw - w) // 2, 0)
        y = py + max((ph - h) // 2, 0)
        self.geometry(f"+{x}+{y}")
