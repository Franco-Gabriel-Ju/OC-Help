import os
import sys
import math


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
from conversor import convertir_nc_a_nc
from conversor import descomplementar


class CalculadoraConversorApp:
    BASES = {"DEC": 10, "BIN": 2, "HEX": 16, "OCT": 8}

    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora Fisica de Conversion")
        self.root.geometry("1180x860")
        self.root.minsize(1040, 760)
        self.root.configure(bg="#111820")

        self.base_activa_var = tk.StringVar(value="DEC")
        self.entrada_var = tk.StringVar(value="")
        self.precision_var = tk.IntVar(value=4)
        self.redondear_var = tk.BooleanVar(value=True)
        self.entrada_complementada_var = tk.BooleanVar(value=False)
        self.nc_fijo_var = tk.BooleanVar(value=False)
        self.nc_base_var = tk.StringVar(value="DEC")
        self.nc_enteras_var = tk.IntVar(value=5)
        self.nc_fracc_var = tk.IntVar(value=2)
        self.separador_var = tk.StringVar(value=",")
        self.complemento_var = tk.BooleanVar(value=False)
        self.estado_var = tk.StringVar(value="Listo. Escribe un numero y se convierte a todas las bases.")
        self.abreviacion_var = tk.StringVar(value="")
        self.nc2nc_entrada_var = tk.StringVar(value="")
        self.nc2nc_origen_base_var = tk.StringVar(value="HEX")
        self.nc2nc_origen_e_var = tk.IntVar(value=4)
        self.nc2nc_origen_f_var = tk.IntVar(value=3)
        self.nc2nc_dest_base_var = tk.StringVar(value="OCT")
        self.nc2nc_dest_e_var = tk.IntVar(value=6)
        self.nc2nc_dest_f_var = tk.IntVar(value=2)
        self.nc2nc_resultado_var = tk.StringVar(value="")
        self.nc2cs_entrada_var = tk.StringVar(value="")
        self.nc2cs_base_var = tk.StringVar(value="HEX")
        self.nc2cs_e_var = tk.IntVar(value=4)
        self.nc2cs_f_var = tk.IntVar(value=3)
        self.nc2cs_resultado_var = tk.StringVar(value="")
        
        self.suma_operando1_var = tk.StringVar(value="")
        self.suma_operando2_var = tk.StringVar(value="")
        self.suma_resultado_var = tk.StringVar(value="")
        self.suma_resultado_explicito_var = tk.StringVar(value="")
        self.suma_base_var = tk.StringVar(value="DEC")
        self.suma_enteras_var = tk.IntVar(value=5)
        self.suma_fracc_var = tk.IntVar(value=2)
        
        self.vista_var = tk.StringVar(value="calc")

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
        self.redondear_var.trace_add("write", lambda *_: self._on_redondeo_change())
        self.entrada_complementada_var.trace_add("write", lambda *_: self._convertir_todo())
        self.nc_fijo_var.trace_add("write", lambda *_: self._on_nc_fijo_change())
        self.nc_base_var.trace_add("write", lambda *_: self._convertir_todo())
        self.nc_enteras_var.trace_add("write", lambda *_: self._convertir_todo())
        self.nc_fracc_var.trace_add("write", lambda *_: self._convertir_todo())
        self.separador_var.trace_add("write", lambda *_: self._convertir_todo())
        self.complemento_var.trace_add("write", lambda *_: self._convertir_todo())
        self.base_activa_var.trace_add("write", lambda *_: self._on_base_change())

    def _build_ui(self):
        main = tk.Frame(self.root, bg="#111820", padx=16, pady=14)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(4, weight=1)

        title = tk.Label(
            main,
            text="Calculadora de Conversion",
            bg="#111820",
            fg="#eaf2ff",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        subtitle = tk.Label(
            main,
            text="Entrada unica, conversion instantanea en DEC/BIN/HEX/OCT.",
            bg="#111820",
            fg="#93b2cf",
            font=("Segoe UI", 12),
        )
        subtitle.grid(row=0, column=0, sticky="e", pady=(0, 10))

        control_bar = tk.Frame(main, bg="#111820")
        control_bar.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        control_bar.grid_columnconfigure(0, weight=1)

        tk.Checkbutton(
            control_bar,
            text="Redondear",
            variable=self.redondear_var,
            bg="#111820",
            fg="#ecf5ff",
            activebackground="#111820",
            activeforeground="#ecf5ff",
            selectcolor="#1c2a38",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        tk.Label(control_bar, text="Fracciones", bg="#111820", fg="#bdd0e7", font=("Segoe UI", 11)).grid(row=0, column=1, padx=(0, 6), sticky="w")
        self.precision_spin = tk.Spinbox(
            control_bar,
            from_=0,
            to=16,
            width=5,
            textvariable=self.precision_var,
            font=("Segoe UI", 12),
            justify="center",
        )
        self.precision_spin.grid(row=0, column=2, sticky="w")

        tk.Label(control_bar, text="Sep.", bg="#111820", fg="#bdd0e7", font=("Segoe UI", 11)).grid(row=0, column=3, padx=(14, 6))
        ttk.Combobox(control_bar, textvariable=self.separador_var, values=[",", "."], state="readonly", width=4).grid(
            row=0, column=4
        )

        tk.Checkbutton(
            control_bar,
            text="Valor ya complementado",
            variable=self.entrada_complementada_var,
            bg="#111820",
            fg="#ecf5ff",
            activebackground="#111820",
            activeforeground="#ecf5ff",
            selectcolor="#1c2a38",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=5, padx=(14, 0))

        tk.Checkbutton(
            control_bar,
            text="NC fijo",
            variable=self.nc_fijo_var,
            bg="#111820",
            fg="#ecf5ff",
            activebackground="#111820",
            activeforeground="#ecf5ff",
            selectcolor="#1c2a38",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=6, padx=(14, 0))

        tk.Label(control_bar, text="B", bg="#111820", fg="#bdd0e7", font=("Segoe UI", 11)).grid(row=0, column=7, padx=(8, 4))
        self.nc_base_combo = ttk.Combobox(
            control_bar,
            textvariable=self.nc_base_var,
            values=("DEC", "BIN", "HEX", "OCT"),
            state="disabled",
            width=6,
        )
        self.nc_base_combo.grid(row=0, column=8, sticky="w")

        tk.Label(control_bar, text="E", bg="#111820", fg="#bdd0e7", font=("Segoe UI", 11)).grid(row=0, column=9, padx=(8, 4))
        self.nc_enteras_spin = tk.Spinbox(
            control_bar,
            from_=1,
            to=32,
            width=5,
            textvariable=self.nc_enteras_var,
            font=("Segoe UI", 12),
            justify="center",
            state="disabled",
        )
        self.nc_enteras_spin.grid(row=0, column=10, sticky="w")

        tk.Label(control_bar, text="F", bg="#111820", fg="#bdd0e7", font=("Segoe UI", 11)).grid(row=0, column=11, padx=(8, 4))
        self.nc_fracc_spin = tk.Spinbox(
            control_bar,
            from_=0,
            to=16,
            width=5,
            textvariable=self.nc_fracc_var,
            font=("Segoe UI", 12),
            justify="center",
            state="disabled",
        )
        self.nc_fracc_spin.grid(row=0, column=12, sticky="w")

        tk.Checkbutton(
            control_bar,
            text="Aplicar complemento",
            variable=self.complemento_var,
            bg="#111820",
            fg="#ecf5ff",
            activebackground="#111820",
            activeforeground="#ecf5ff",
            selectcolor="#1c2a38",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=13, padx=(14, 0))

        nav_bar = tk.Frame(main, bg="#111820")
        nav_bar.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        self.tab_calc_btn = tk.Button(
            nav_bar,
            text="Calculadora",
            command=lambda: self._set_view("calc"),
            bg="#2d5f99",
            fg="#ffffff",
            activebackground="#3b77b8",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            font=("Segoe UI", 11, "bold"),
        )
        self.tab_calc_btn.grid(row=0, column=0, padx=(0, 6))

        self.tab_nc2nc_btn = tk.Button(
            nav_bar,
            text="NC -> NC",
            command=lambda: self._set_view("nc2nc"),
            bg="#2a3d53",
            fg="#d7e6f8",
            activebackground="#3a526f",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            font=("Segoe UI", 11, "bold"),
        )
        self.tab_nc2nc_btn.grid(row=0, column=1, padx=6)

        self.tab_nc2cs_btn = tk.Button(
            nav_bar,
            text="NC -> CS",
            command=lambda: self._set_view("nc2cs"),
            bg="#2a3d53",
            fg="#d7e6f8",
            activebackground="#3a526f",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            font=("Segoe UI", 11, "bold"),
        )
        self.tab_nc2cs_btn.grid(row=0, column=2, padx=6)

        self.input_frame = tk.Frame(main, bg="#182330", bd=0, highlightthickness=1, highlightbackground="#2f435a")
        self.input_frame.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        self.input_frame.grid_columnconfigure(1, weight=1)
        self.input_frame.grid_columnconfigure(3, weight=0)

        tk.Label(self.input_frame, text="Entrada", bg="#182330", fg="#9ec0df", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, padx=10, pady=8
        )
        self.entrada_entry = tk.Entry(
            self.input_frame,
            textvariable=self.entrada_var,
            bg="#1f2f42",
            fg="#f6fbff",
            insertbackground="#f6fbff",
            relief="flat",
            bd=0,
            font=("Consolas", 30, "bold"),
            justify="right",
        )
        self.entrada_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=8)

        tk.Label(self.input_frame, text="Base", bg="#182330", fg="#9ec0df", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=2, padx=(0, 6), pady=8
        )
        ttk.Combobox(
            self.input_frame,
            textvariable=self.base_activa_var,
            values=("DEC", "BIN", "HEX", "OCT"),
            state="readonly",
            width=8,
        ).grid(row=0, column=3, padx=(0, 10), pady=8)

        self.center = tk.Frame(main, bg="#111820")
        self.center.grid(row=4, column=0, sticky="nsew")
        self.center.grid_columnconfigure(0, weight=6)
        self.center.grid_columnconfigure(1, weight=5)
        self.center.grid_rowconfigure(0, weight=1)

        output_frame = tk.Frame(self.center, bg="#15202d", padx=8, pady=8)
        output_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        output_frame.grid_columnconfigure(1, weight=1)
        for rr in range(4):
            output_frame.grid_rowconfigure(rr, weight=1)

        label_colors = {"DEC": "#df2670", "BIN": "#29ad95", "HEX": "#2476a4", "OCT": "#6d8f35"}
        row = 0
        for key in ("DEC", "BIN", "HEX", "OCT"):
            tk.Label(
                output_frame,
                text=key,
                bg=label_colors[key],
                fg="#ffffff",
                width=7,
                pady=8,
                font=("Segoe UI", 14, "bold"),
            ).grid(row=row, column=0, sticky="nsew", pady=2)

            entry = tk.Entry(
                output_frame,
                textvariable=self.salida_vars[key],
                bg="#d7eadf",
                fg="#00111c",
                readonlybackground="#d7eadf",
                relief="flat",
                bd=0,
                font=("Consolas", 22, "bold"),
                justify="right",
            )
            entry.grid(row=row, column=1, sticky="nsew", padx=(4, 4), pady=2, ipady=10)
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
            ).grid(row=row, column=2, sticky="nsew", pady=2)
            row += 1

        keypad = tk.Frame(self.center, bg="#121a23", padx=8, pady=8)
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
                    font=("Segoe UI", 16, "bold") if len(key) <= 2 else ("Segoe UI", 12, "bold"),
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
                if key in "0123456789ABCDEF":
                    self._digit_buttons[key] = btn

        self.abreviacion_lbl = tk.Label(
            main,
            textvariable=self.abreviacion_var,
            bg="#111820",
            fg="#b9d0e8",
            anchor="w",
            font=("Consolas", 15, "bold"),
        )
        self.abreviacion_lbl.grid(row=5, column=0, sticky="ew", pady=(8, 0))

        self.suma_frame = tk.Frame(main, bg="#1a2f4a", bd=0, highlightthickness=1, highlightbackground="#2c4058", padx=12, pady=12)
        self.suma_frame.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        self.suma_frame.grid_columnconfigure(1, weight=1)
        self.suma_frame.grid_columnconfigure(3, weight=1)

        tk.Label(
            self.suma_frame,
            text="Suma en NC Fijo",
            bg="#1a2f4a",
            fg="#d9e9f8",
            font=("Segoe UI", 13, "bold"),
        ).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))

        tk.Label(self.suma_frame, text="Operando 1 (comp.)", bg="#1a2f4a", fg="#b8cde2", font=("Segoe UI", 10)).grid(row=1, column=0, padx=(0, 6), sticky="w")
        tk.Entry(
            self.suma_frame,
            textvariable=self.suma_operando1_var,
            bg="#1f2f42",
            fg="#f6fbff",
            insertbackground="#f6fbff",
            relief="flat",
            bd=0,
            font=("Consolas", 12, "bold"),
            width=16,
            justify="right",
        ).grid(row=1, column=1, padx=(0, 12), sticky="ew")

        tk.Label(self.suma_frame, text="Operando 2 (comp.)", bg="#1a2f4a", fg="#b8cde2", font=("Segoe UI", 10)).grid(row=1, column=2, padx=(0, 6), sticky="w")
        tk.Entry(
            self.suma_frame,
            textvariable=self.suma_operando2_var,
            bg="#1f2f42",
            fg="#f6fbff",
            insertbackground="#f6fbff",
            relief="flat",
            bd=0,
            font=("Consolas", 12, "bold"),
            width=16,
            justify="right",
        ).grid(row=1, column=3, padx=(0, 12), sticky="ew")

        tk.Label(self.suma_frame, text="B", bg="#1a2f4a", fg="#b8cde2", font=("Segoe UI", 10)).grid(row=1, column=4, sticky="w")
        ttk.Combobox(self.suma_frame, textvariable=self.suma_base_var, values=("DEC", "BIN", "HEX", "OCT"), state="readonly", width=5).grid(row=1, column=5, padx=(0, 12), sticky="w")

        tk.Label(self.suma_frame, text="E", bg="#1a2f4a", fg="#b8cde2", font=("Segoe UI", 10)).grid(row=2, column=0, padx=(0, 6), sticky="w")
        tk.Spinbox(self.suma_frame, from_=1, to=32, width=4, textvariable=self.suma_enteras_var, justify="center", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w")

        tk.Label(self.suma_frame, text="F", bg="#1a2f4a", fg="#b8cde2", font=("Segoe UI", 10)).grid(row=2, column=2, padx=(0, 6), sticky="w")
        tk.Spinbox(self.suma_frame, from_=0, to=16, width=4, textvariable=self.suma_fracc_var, justify="center", font=("Segoe UI", 10)).grid(row=2, column=3, sticky="w")

        tk.Button(
            self.suma_frame,
            text="Sumar",
            command=self._sumar_nc,
            bg="#3f7d63",
            fg="#f6fffb",
            activebackground="#4f9a7b",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=12,
            font=("Segoe UI", 11, "bold"),
        ).grid(row=2, column=4, columnspan=2, sticky="ew", padx=(12, 0))

        tk.Label(self.suma_frame, text="Resultado (comp.)", bg="#1a2f4a", fg="#b8cde2", font=("Segoe UI", 10)).grid(row=3, column=0, padx=(0, 6), sticky="w", pady=(8, 0))
        tk.Entry(
            self.suma_frame,
            textvariable=self.suma_resultado_var,
            state="readonly",
            readonlybackground="#d7eadf",
            fg="#00111c",
            relief="flat",
            bd=0,
            font=("Consolas", 14, "bold"),
            width=18,
            justify="right",
        ).grid(row=3, column=1, columnspan=1, sticky="ew", padx=(0, 12), pady=(8, 0))

        tk.Label(self.suma_frame, text="Explicito", bg="#1a2f4a", fg="#b8cde2", font=("Segoe UI", 10)).grid(row=3, column=2, padx=(0, 6), sticky="w", pady=(8, 0))
        tk.Entry(
            self.suma_frame,
            textvariable=self.suma_resultado_explicito_var,
            state="readonly",
            readonlybackground="#f0e6d8",
            fg="#00111c",
            relief="flat",
            bd=0,
            font=("Consolas", 12, "bold"),
            width=18,
            justify="right",
        ).grid(row=3, column=3, columnspan=3, sticky="ew", pady=(8, 0))

        self.nc2nc_frame = tk.Frame(main, bg="#162433", bd=0, highlightthickness=1, highlightbackground="#2c4058", padx=16, pady=16)
        self.nc2nc_frame.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        self.nc2nc_frame.grid_columnconfigure(0, weight=1)
        self.nc2nc_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            self.nc2nc_frame,
            text="Conversion NC -> NC",
            bg="#162433",
            fg="#d9e9f8",
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(
            self.nc2nc_frame,
            text="Convierte directamente entre dos sistemas complementados fijos (B,E,F).",
            bg="#162433",
            fg="#a8c5df",
            font=("Segoe UI", 11),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        origen_box = tk.Frame(self.nc2nc_frame, bg="#1b3047", padx=10, pady=10)
        origen_box.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        origen_box.grid_columnconfigure(1, weight=1)

        destino_box = tk.Frame(self.nc2nc_frame, bg="#1b3047", padx=10, pady=10)
        destino_box.grid(row=2, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(origen_box, text="Origen NC", bg="#1b3047", fg="#d9e9f8", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))
        tk.Label(origen_box, text="Entrada comp.", bg="#1b3047", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=1, column=0, padx=(0, 6), sticky="w")
        tk.Entry(
            origen_box,
            textvariable=self.nc2nc_entrada_var,
            bg="#1f2f42",
            fg="#f6fbff",
            insertbackground="#f6fbff",
            relief="flat",
            bd=0,
            font=("Consolas", 14, "bold"),
            width=18,
            justify="right",
        ).grid(row=1, column=1, columnspan=5, padx=(0, 10), sticky="ew")

        tk.Label(origen_box, text="B", bg="#1b3047", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=2, column=0, pady=(8, 0), sticky="w")
        ttk.Combobox(origen_box, textvariable=self.nc2nc_origen_base_var, values=("DEC", "BIN", "HEX", "OCT"), state="readonly", width=6).grid(row=2, column=1, pady=(8, 0), sticky="w")
        tk.Label(origen_box, text="E", bg="#1b3047", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=2, column=2, padx=(10, 2), pady=(8, 0), sticky="w")
        tk.Spinbox(origen_box, from_=1, to=32, width=4, textvariable=self.nc2nc_origen_e_var, justify="center", font=("Segoe UI", 11)).grid(row=2, column=3, pady=(8, 0), sticky="w")
        tk.Label(origen_box, text="F", bg="#1b3047", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=2, column=4, padx=(10, 2), pady=(8, 0), sticky="w")
        tk.Spinbox(origen_box, from_=0, to=16, width=4, textvariable=self.nc2nc_origen_f_var, justify="center", font=("Segoe UI", 11)).grid(row=2, column=5, pady=(8, 0), sticky="w")

        tk.Label(destino_box, text="Destino NC", bg="#1b3047", fg="#d9e9f8", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))
        tk.Label(destino_box, text="B", bg="#1b3047", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w")
        ttk.Combobox(destino_box, textvariable=self.nc2nc_dest_base_var, values=("DEC", "BIN", "HEX", "OCT"), state="readonly", width=6).grid(row=1, column=1, sticky="w")
        tk.Label(destino_box, text="E", bg="#1b3047", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=1, column=2, padx=(10, 2), sticky="w")
        tk.Spinbox(destino_box, from_=1, to=32, width=4, textvariable=self.nc2nc_dest_e_var, justify="center", font=("Segoe UI", 11)).grid(row=1, column=3, sticky="w")
        tk.Label(destino_box, text="F", bg="#1b3047", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=1, column=4, padx=(10, 2), sticky="w")
        tk.Spinbox(destino_box, from_=0, to=16, width=4, textvariable=self.nc2nc_dest_f_var, justify="center", font=("Segoe UI", 11)).grid(row=1, column=5, sticky="w")

        tk.Button(
            origen_box,
            text="Tomar entrada actual",
            command=self._nc2nc_tomar_entrada_actual,
            bg="#2f4c67",
            fg="#ecf5ff",
            activebackground="#426789",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(12, 0))

        tk.Button(
            destino_box,
            text="Convertir NC->NC",
            command=self._nc2nc_convertir,
            bg="#3f7d63",
            fg="#f6fffb",
            activebackground="#4f9a7b",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(12, 0))

        tk.Label(destino_box, text="Resultado", bg="#1b3047", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=3, column=0, padx=(0, 6), pady=(12, 0), sticky="w")
        tk.Entry(
            destino_box,
            textvariable=self.nc2nc_resultado_var,
            state="readonly",
            readonlybackground="#d7eadf",
            fg="#00111c",
            relief="flat",
            bd=0,
            font=("Consolas", 16, "bold"),
            width=18,
            justify="right",
        ).grid(row=3, column=1, columnspan=5, sticky="ew", pady=(12, 0))

        self.nc2cs_frame = tk.Frame(main, bg="#162433", bd=0, highlightthickness=1, highlightbackground="#2c4058", padx=16, pady=16)
        self.nc2cs_frame.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        self.nc2cs_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            self.nc2cs_frame,
            text="Conversion NC -> CS (signo explicito)",
            bg="#162433",
            fg="#d9e9f8",
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, columnspan=11, sticky="w", pady=(0, 6))

        tk.Label(
            self.nc2cs_frame,
            text="Transforma un valor complementado fijo a notación con signo explícito.",
            bg="#162433",
            fg="#a8c5df",
            font=("Segoe UI", 11),
        ).grid(row=1, column=0, columnspan=11, sticky="w", pady=(0, 12))

        tk.Label(self.nc2cs_frame, text="Entrada comp.", bg="#162433", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=2, column=0, padx=(0, 6), sticky="w")
        tk.Entry(
            self.nc2cs_frame,
            textvariable=self.nc2cs_entrada_var,
            bg="#1f2f42",
            fg="#f6fbff",
            insertbackground="#f6fbff",
            relief="flat",
            bd=0,
            font=("Consolas", 15, "bold"),
            width=18,
            justify="right",
        ).grid(row=2, column=1, padx=(0, 10), sticky="w")

        tk.Label(self.nc2cs_frame, text="Base", bg="#162433", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=2, column=2, padx=(0, 4), sticky="w")
        ttk.Combobox(self.nc2cs_frame, textvariable=self.nc2cs_base_var, values=("DEC", "BIN", "HEX", "OCT"), state="readonly", width=6).grid(row=2, column=3, sticky="w")
        tk.Label(self.nc2cs_frame, text="E", bg="#162433", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=2, column=4, padx=(8, 2), sticky="w")
        tk.Spinbox(self.nc2cs_frame, from_=1, to=32, width=4, textvariable=self.nc2cs_e_var, justify="center", font=("Segoe UI", 11)).grid(row=2, column=5, sticky="w")
        tk.Label(self.nc2cs_frame, text="F", bg="#162433", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=2, column=6, padx=(8, 2), sticky="w")
        tk.Spinbox(self.nc2cs_frame, from_=0, to=16, width=4, textvariable=self.nc2cs_f_var, justify="center", font=("Segoe UI", 11)).grid(row=2, column=7, sticky="w")

        tk.Button(
            self.nc2cs_frame,
            text="Tomar entrada actual",
            command=self._nc2cs_tomar_entrada_actual,
            bg="#2f4c67",
            fg="#ecf5ff",
            activebackground="#426789",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(12, 0))

        tk.Button(
            self.nc2cs_frame,
            text="Convertir NC->CS",
            command=self._nc2cs_convertir,
            bg="#3f7d63",
            fg="#f6fffb",
            activebackground="#4f9a7b",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
        ).grid(row=3, column=3, columnspan=3, sticky="w", pady=(12, 0))

        tk.Label(self.nc2cs_frame, text="Resultado", bg="#162433", fg="#b8cde2", font=("Segoe UI", 11)).grid(row=3, column=6, padx=(10, 6), pady=(12, 0), sticky="w")
        tk.Entry(
            self.nc2cs_frame,
            textvariable=self.nc2cs_resultado_var,
            state="readonly",
            readonlybackground="#d7eadf",
            fg="#00111c",
            relief="flat",
            bd=0,
            font=("Consolas", 16, "bold"),
            width=22,
            justify="right",
        ).grid(row=3, column=7, columnspan=4, sticky="w", pady=(12, 0))

        status = tk.Label(main, textvariable=self.estado_var, bg="#111820", fg="#95b0cb", anchor="w", font=("Segoe UI", 11))
        status.grid(row=8, column=0, sticky="ew", pady=(6, 0))

        self._set_view("calc")

        self.root.bind("<Return>", lambda _e: self._convertir_todo())
        self.entrada_entry.focus_set()

    def _on_base_change(self):
        self._refresh_digit_buttons()
        self._convertir_todo()
        self.estado_var.set(f"Base de entrada activa: {self.base_activa_var.get()}")

    def _on_redondeo_change(self):
        if self.redondear_var.get():
            self.precision_spin.configure(state="normal")
        else:
            self.precision_spin.configure(state="disabled")
        self._convertir_todo()

    def _on_nc_fijo_change(self):
        state = "normal" if self.nc_fijo_var.get() else "disabled"
        self.nc_base_combo.configure(state=state)
        self.nc_enteras_spin.configure(state=state)
        self.nc_fracc_spin.configure(state=state)
        self._convertir_todo()

    def _set_view(self, view):
        self.vista_var.set(view)

        for btn in (self.tab_calc_btn, self.tab_nc2nc_btn, self.tab_nc2cs_btn):
            btn.configure(bg="#2a3d53", fg="#d7e6f8")

        if view == "calc":
            self.tab_calc_btn.configure(bg="#2d5f99", fg="#ffffff")
            self.input_frame.grid(row=3, column=0, sticky="ew")
            self.center.grid(row=4, column=0, sticky="nsew", pady=(8, 0))
            self.abreviacion_lbl.grid(row=5, column=0, sticky="ew", pady=(8, 0))
            self.nc2nc_frame.grid_remove()
            self.nc2cs_frame.grid_remove()
            self.estado_var.set("Vista Calculadora.")
            return

        if view == "nc2nc":
            self.tab_nc2nc_btn.configure(bg="#2d5f99", fg="#ffffff")
            self.input_frame.grid_remove()
            self.center.grid_remove()
            self.abreviacion_lbl.grid_remove()
            self.nc2cs_frame.grid_remove()
            self.nc2nc_frame.grid(row=4, column=0, sticky="nsew", pady=(8, 0))
            self.estado_var.set("Vista NC -> NC.")
            return

        self.tab_nc2cs_btn.configure(bg="#2d5f99", fg="#ffffff")
        self.input_frame.grid_remove()
        self.center.grid_remove()
        self.abreviacion_lbl.grid_remove()
        self.nc2nc_frame.grid_remove()
        self.nc2cs_frame.grid(row=4, column=0, sticky="nsew", pady=(8, 0))
        self.estado_var.set("Vista NC -> CS.")

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

    def _nc2nc_tomar_entrada_actual(self):
        self.nc2nc_entrada_var.set(self.entrada_var.get().strip())
        self.nc2nc_origen_base_var.set(self.base_activa_var.get())
        if self.nc_fijo_var.get():
            self.nc2nc_origen_e_var.set(self.nc_enteras_var.get())
            self.nc2nc_origen_f_var.set(self.nc_fracc_var.get())
        self.estado_var.set("Entrada actual copiada al panel NC->NC.")

    def _nc2nc_convertir(self):
        try:
            resultado = convertir_nc_a_nc(
                self.nc2nc_entrada_var.get(),
                self.BASES[self.nc2nc_origen_base_var.get()],
                self.nc2nc_origen_e_var.get(),
                self.nc2nc_origen_f_var.get(),
                self.BASES[self.nc2nc_dest_base_var.get()],
                self.nc2nc_dest_e_var.get(),
                self.nc2nc_dest_f_var.get(),
                separador=self.separador_var.get(),
            )
        except ConversionError as exc:
            self.nc2nc_resultado_var.set("")
            self.estado_var.set(f"Error NC->NC: {exc}")
            return

        self.nc2nc_resultado_var.set(resultado)
        self.estado_var.set("Conversion NC->NC calculada.")

    def _nc2cs_tomar_entrada_actual(self):
        self.nc2cs_entrada_var.set(self.entrada_var.get().strip())
        self.nc2cs_base_var.set(self.base_activa_var.get())
        if self.nc_fijo_var.get():
            self.nc2cs_e_var.set(self.nc_enteras_var.get())
            self.nc2cs_f_var.set(self.nc_fracc_var.get())
        self.estado_var.set("Entrada actual copiada al panel NC->CS.")

    def _nc2cs_convertir(self):
        try:
            resultado = descomplementar(
                self.nc2cs_entrada_var.get(),
                self.BASES[self.nc2cs_base_var.get()],
                separador=self.separador_var.get(),
                enteros_totales=self.nc2cs_e_var.get(),
                fracc_fijas=self.nc2cs_f_var.get(),
            )
        except ConversionError as exc:
            self.nc2cs_resultado_var.set("")
            self.estado_var.set(f"Error NC->CS: {exc}")
            return

        self.nc2cs_resultado_var.set(resultado)
        self.estado_var.set("Conversion NC->CS calculada.")

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

    def _abreviacion_nc(self, numero_entrada, base_origen, separador):
        texto = numero_entrada.strip().upper().replace(",", ".")
        if texto.startswith("+") or texto.startswith("-"):
            texto = texto[1:]

        if "." in texto:
            parte_entera, parte_fraccion = texto.split(".", 1)
        else:
            parte_entera, parte_fraccion = texto, ""

        if not parte_entera:
            parte_entera = "0"

        # x: ancho en bits aproximado redondeado al siguiente multiplo de 8.
        if base_origen == 2:
            bits_por_digito = 1
        elif base_origen == 8:
            bits_por_digito = 3
        elif base_origen == 16:
            bits_por_digito = 4
        else:
            bits_por_digito = math.ceil(math.log2(base_origen))

        bits_aprox = len(parte_entera) * bits_por_digito
        ancho_bits = max(1, math.ceil(bits_aprox / 8) * 8)

        numero_formateado = parte_entera
        if parte_fraccion:
            numero_formateado += f"{separador}{parte_fraccion}"

        return f"{numero_formateado} ({ancho_bits},{len(parte_entera)},{len(parte_fraccion)})NC"

    def _precision_minima_exacta(self, numero_entrada, base_origen, base_destino):
        """Calcula precision minima para no perder informacion exacta en 2/8/16."""
        bits_por_digito = {2: 1, 8: 3, 16: 4}
        if base_origen not in bits_por_digito or base_destino not in bits_por_digito:
            return 0

        texto = numero_entrada.strip().upper().replace(",", ".")
        if texto.startswith("+") or texto.startswith("-"):
            texto = texto[1:]
        if "." not in texto:
            return 0

        frac_len_origen = len(texto.split(".", 1)[1])
        if frac_len_origen <= 0:
            return 0

        return math.ceil(frac_len_origen * bits_por_digito[base_origen] / bits_por_digito[base_destino])

    def _ajustar_salida_fraccion_binaria(self, salida, numero_entrada, base_origen, base_destino, separador):
        """Recorta ceros fraccionarios sobrantes para conversiones 2/8/16.

        Ejemplo: FE.54 (hex) -> octal puede producir 5300 por precision global,
        pero la longitud exacta por agrupacion de bits es 3: 530.
        """
        bits_por_digito = {2: 1, 8: 3, 16: 4}
        if base_origen not in bits_por_digito or base_destino not in bits_por_digito:
            return salida

        texto = numero_entrada.strip().upper().replace(",", ".")
        if texto.startswith("+") or texto.startswith("-"):
            texto = texto[1:]

        if "." not in texto:
            return salida

        frac_len_origen = len(texto.split(".", 1)[1])
        if frac_len_origen == 0:
            return salida

        min_digitos = math.ceil(frac_len_origen * bits_por_digito[base_origen] / bits_por_digito[base_destino])
        if min_digitos <= 0 or separador not in salida:
            return salida

        parte_entera, parte_frac = salida.split(separador, 1)
        if len(parte_frac) <= min_digitos:
            return salida

        sobrante = parte_frac[min_digitos:]
        if any(ch != "0" for ch in sobrante):
            return salida

        return f"{parte_entera}{separador}{parte_frac[:min_digitos]}"

    def _convertir_todo(self):
        numero = self.entrada_var.get().strip().upper()
        if not numero or numero in ("-", "+"):
            self._clear_outputs()
            self.abreviacion_var.set("")
            return

        base_origen = self.BASES[self.base_activa_var.get()]
        precision = self.precision_var.get()
        separador = self.separador_var.get()
        complemento = "complemento" if self.complemento_var.get() else None
        enteros_fijos = self.nc_enteras_var.get() if self.nc_fijo_var.get() else None
        fracc_fijas = self.nc_fracc_var.get() if self.nc_fijo_var.get() else None
        nc_base_fija = self.BASES[self.nc_base_var.get()] if self.nc_fijo_var.get() else None

        # Si la entrada ya viene complementada, primero la descomplementamos.
        if self.entrada_complementada_var.get():
            numero = descomplementar(
                numero,
                base_origen,
                separador=separador,
                enteros_totales=enteros_fijos,
                fracc_fijas=fracc_fijas,
            )
            complemento = None

        try:
            self.abreviacion_var.set(self._abreviacion_nc(numero, base_origen, separador))
            for key, base_dest in self.BASES.items():
                if self.redondear_var.get():
                    precision_base = fracc_fijas if fracc_fijas is not None else precision
                    precision_objetivo = max(precision_base, self._precision_minima_exacta(numero, base_origen, base_dest))
                else:
                    precision_objetivo = max(16, self._precision_minima_exacta(numero, base_origen, base_dest))
                salida = convertir(
                    numero,
                    base_origen,
                    base_dest,
                    precision=precision_objetivo,
                    complemento=complemento,
                    bits_complemento=None,
                    separador=separador,
                    enteros_valor_fijos=(enteros_fijos - 1)
                    if enteros_fijos is not None and complemento and base_dest == nc_base_fija
                    else None,
                )
                salida = self._ajustar_salida_fraccion_binaria(salida, numero, base_origen, base_dest, separador)
                self.salida_vars[key].set(salida)
            self.estado_var.set("Conversion actualizada en DEC, BIN, HEX y OCT.")
        except ConversionError as exc:
            self._clear_outputs()
            self.abreviacion_var.set("")
            self.estado_var.set(f"Error: {exc}")


def main():
    root = tk.Tk()
    CalculadoraConversorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
