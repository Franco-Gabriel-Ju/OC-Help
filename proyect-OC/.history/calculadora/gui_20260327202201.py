import os
import sys


def _bootstrap_tk_libraries():
    if os.environ.get("TCL_LIBRARY") and os.environ.get("TK_LIBRARY"):
        return

    candidate_roots = []
    for root in (getattr(sys, "base_prefix", ""), getattr(sys, "exec_prefix", ""), os.path.dirname(sys.executable)):
        if root and root not in candidate_roots:
            candidate_roots.append(root)

    for root in candidate_roots:
        tcl_dir = os.path.join(root, "tcl", "tcl8.6")
        tk_dir = os.path.join(root, "tcl", "tk8.6")

        if os.path.isfile(os.path.join(tcl_dir, "init.tcl")):
            os.environ.setdefault("TCL_LIBRARY", tcl_dir)
        if os.path.isfile(os.path.join(tk_dir, "tk.tcl")):
            os.environ.setdefault("TK_LIBRARY", tk_dir)

        if os.environ.get("TCL_LIBRARY") and os.environ.get("TK_LIBRARY"):
            return


_bootstrap_tk_libraries()

import tkinter as tk
from tkinter import ttk

from conversor import ConversionError, convertir


class CalculadoraConversorApp:
    BASES = {"DEC": 10, "BIN": 2, "HEX": 16, "OCT": 8}

    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora Fisica de Conversion")
        self.root.geometry("900x700")
        self.root.minsize(820, 620)
        self.root.configure(bg="#111820")

        self.base_activa_var = tk.StringVar(value="DEC")
        self.entrada_var = tk.StringVar(value="")
        self.precision_var = tk.IntVar(value=4)
        self.separador_var = tk.StringVar(value=",")
        self.complemento_var = tk.BooleanVar(value=False)
        self.estado_var = tk.StringVar(value="Listo. Escribe un numero y se convierte a todas las bases.")

        self.salida_vars = {
            "DEC": tk.StringVar(value=""),
            "BIN": tk.StringVar(value=""),
            "HEX": tk.StringVar(value=""),
            "OCT": tk.StringVar(value=""),
        }

        self._digit_buttons = {}
        self._build_ui()
        self._refresh_digit_buttons()

        self.entrada_var.trace_add("write", lambda *_: self._convertir_todo())
        self.precision_var.trace_add("write", lambda *_: self._convertir_todo())
        self.separador_var.trace_add("write", lambda *_: self._convertir_todo())
        self.complemento_var.trace_add("write", lambda *_: self._convertir_todo())
        self.base_activa_var.trace_add("write", lambda *_: self._on_base_change())

    def _build_ui(self):
        main = tk.Frame(self.root, bg="#111820", padx=16, pady=14)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(3, weight=1)

        title = tk.Label(
            main,
            text="Calculadora de Conversion",
            bg="#111820",
            fg="#eaf2ff",
            font=("Segoe UI", 19, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        control_bar = tk.Frame(main, bg="#111820")
        control_bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        control_bar.grid_columnconfigure(0, weight=1)

        tk.Label(control_bar, text="Precision", bg="#111820", fg="#bdd0e7").grid(row=0, column=0, padx=(0, 6), sticky="w")
        tk.Spinbox(
            control_bar,
            from_=0,
            to=16,
            width=4,
            textvariable=self.precision_var,
            font=("Segoe UI", 10),
            justify="center",
        ).grid(row=0, column=1, sticky="w")

        tk.Label(control_bar, text="Sep.", bg="#111820", fg="#bdd0e7").grid(row=0, column=2, padx=(14, 6))
        ttk.Combobox(control_bar, textvariable=self.separador_var, values=[",", "."], state="readonly", width=3).grid(
            row=0, column=3
        )

        tk.Checkbutton(
            control_bar,
            text="Complemento",
            variable=self.complemento_var,
            bg="#111820",
            fg="#ecf5ff",
            activebackground="#111820",
            activeforeground="#ecf5ff",
            selectcolor="#1c2a38",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=4, padx=(14, 0))

        input_frame = tk.Frame(main, bg="#182330", bd=0, highlightthickness=1, highlightbackground="#2f435a")
        input_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(3, weight=0)

        tk.Label(input_frame, text="Entrada", bg="#182330", fg="#9ec0df", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, padx=10, pady=8
        )
        self.entrada_entry = tk.Entry(
            input_frame,
            textvariable=self.entrada_var,
            bg="#1f2f42",
            fg="#f6fbff",
            insertbackground="#f6fbff",
            relief="flat",
            bd=0,
            font=("Consolas", 24, "bold"),
            justify="right",
        )
        self.entrada_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=8)

        tk.Label(input_frame, text="Base", bg="#182330", fg="#9ec0df", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=2, padx=(0, 6), pady=8
        )
        ttk.Combobox(
            input_frame,
            textvariable=self.base_activa_var,
            values=("DEC", "BIN", "HEX", "OCT"),
            state="readonly",
            width=6,
        ).grid(row=0, column=3, padx=(0, 10), pady=8)

        center = tk.Frame(main, bg="#111820")
        center.grid(row=3, column=0, sticky="nsew")
        center.grid_columnconfigure(0, weight=5)
        center.grid_columnconfigure(1, weight=4)
        center.grid_rowconfigure(0, weight=1)

        output_frame = tk.Frame(center, bg="#15202d", padx=8, pady=8)
        output_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        output_frame.grid_columnconfigure(1, weight=1)

        label_colors = {"DEC": "#df2670", "BIN": "#29ad95", "HEX": "#2476a4", "OCT": "#6d8f35"}
        row = 0
        for key in ("DEC", "BIN", "HEX", "OCT"):
            tk.Label(
                output_frame,
                text=key,
                bg=label_colors[key],
                fg="#ffffff",
                width=6,
                pady=9,
                font=("Segoe UI", 13, "bold"),
            ).grid(row=row, column=0, sticky="ns", pady=3)

            entry = tk.Entry(
                output_frame,
                textvariable=self.salida_vars[key],
                bg="#d7eadf",
                fg="#00111c",
                readonlybackground="#d7eadf",
                relief="flat",
                bd=0,
                font=("Consolas", 20, "bold"),
                justify="right",
            )
            entry.grid(row=row, column=1, sticky="ew", padx=(4, 4), pady=3, ipady=8)
            entry.configure(state="readonly")

            tk.Button(
                output_frame,
                text="Usar",
                command=lambda b=key: self._usar_salida_como_entrada(b),
                bg="#2e4558",
                fg="#ecf5ff",
                activebackground="#39556d",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=10,
            ).grid(row=row, column=2, sticky="nsew", pady=3)
            row += 1

        keypad = tk.Frame(center, bg="#121a23", padx=8, pady=8)
        keypad.grid(row=0, column=1, sticky="nsew")
        for c in range(4):
            keypad.grid_columnconfigure(c, weight=1)
        for r in range(6):
            keypad.grid_rowconfigure(r, weight=1)

        keys = [
            ["A", "B", "C", "DEL"],
            ["D", "E", "F", "AC"],
            ["7", "8", "9", ","],
            ["4", "5", "6", "."],
            ["1", "2", "3", "+/-"],
            ["0", "-", "Copiar BIN", "Copiar DEC"],
        ]

        for r, row_keys in enumerate(keys):
            for c, key in enumerate(row_keys):
                btn = tk.Button(
                    keypad,
                    text=key,
                    command=lambda k=key: self._on_keypad_press(k),
                    bg="#56a79a" if len(key) == 1 and key.isalnum() else "#82b8ad",
                    fg="#051114",
                    activebackground="#9fc9bf",
                    activeforeground="#000000",
                    relief="flat",
                    bd=0,
                    font=("Segoe UI", 14, "bold") if len(key) <= 2 else ("Segoe UI", 10, "bold"),
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                if key in "0123456789ABCDEF":
                    self._digit_buttons[key] = btn

        status = tk.Label(main, textvariable=self.estado_var, bg="#111820", fg="#95b0cb", anchor="w", font=("Segoe UI", 10))
        status.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        self.root.bind("<Return>", lambda _e: self._convertir_todo())
        self.entrada_entry.focus_set()

    def _on_base_change(self):
        self._refresh_digit_buttons()
        self._convertir_todo()
        self.estado_var.set(f"Base de entrada activa: {self.base_activa_var.get()}")

    def _refresh_digit_buttons(self):
        base = self.BASES[self.base_activa_var.get()]
        if base == 2:
            permitidos = "01"
        elif base == 8:
            permitidos = "01234567"
        elif base == 10:
            permitidos = "0123456789"
        else:
            permitidos = "0123456789ABCDEF"

        for d, btn in self._digit_buttons.items():
            if d in permitidos:
                btn.configure(state="normal", bg="#56a79a", fg="#051114")
            else:
                btn.configure(state="disabled", bg="#5f7b76", fg="#304543")

    def _append(self, token):
        current = self.entrada_var.get()

        if token in ".,":
            if "." in current or "," in current:
                return
            self.entrada_var.set(current + token)
            return

        if token == "-":
            if current.startswith("-"):
                return
            self.entrada_var.set("-" + current)
            return

        self.entrada_var.set(current + token)

    def _toggle_sign(self):
        txt = self.entrada_var.get()
        if not txt:
            self.entrada_var.set("-")
            return
        if txt.startswith("-"):
            self.entrada_var.set(txt[1:])
        else:
            self.entrada_var.set("-" + txt)

    def _on_keypad_press(self, key):
        if key == "AC":
            self.entrada_var.set("")
            self._clear_outputs()
            self.estado_var.set("Listo.")
            return

        if key == "DEL":
            self.entrada_var.set(self.entrada_var.get()[:-1])
            return

        if key == "+/-":
            self._toggle_sign()
            return

        if key == "Copiar BIN":
            self._copy_output("BIN")
            return

        if key == "Copiar DEC":
            self._copy_output("DEC")
            return

        self._append(key)

    def _copy_output(self, base_key):
        value = self.salida_vars[base_key].get().strip()
        if not value:
            self.estado_var.set("No hay valor para copiar.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.estado_var.set(f"Copiado {base_key}: {value}")

    def _usar_salida_como_entrada(self, base_key):
        value = self.salida_vars[base_key].get().strip()
        if not value:
            self.estado_var.set("No hay resultado en esa base.")
            return

        self.base_activa_var.set(base_key)
        self.entrada_var.set(value)
        self.estado_var.set(f"Tomando {base_key} como nueva entrada.")

    def _clear_outputs(self):
        for v in self.salida_vars.values():
            v.set("")

    def _convertir_todo(self):
        numero = self.entrada_var.get().strip().upper()
        if not numero or numero in ("-", "+"):
            self._clear_outputs()
            return

        base_origen = self.BASES[self.base_activa_var.get()]
        precision = self.precision_var.get()
        separador = self.separador_var.get()
        complemento = "complemento" if self.complemento_var.get() else None

        try:
            for key, base_dest in self.BASES.items():
                self.salida_vars[key].set(
                    convertir(
                        numero,
                        base_origen,
                        base_dest,
                        precision=precision,
                        complemento=complemento,
                        bits_complemento=None,
                        separador=separador,
                    )
                )
            self.estado_var.set("Conversion actualizada en DEC, BIN, HEX y OCT.")
        except ConversionError as exc:
            self._clear_outputs()
            self.estado_var.set(f"Error: {exc}")


def main():
    root = tk.Tk()
    CalculadoraConversorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
