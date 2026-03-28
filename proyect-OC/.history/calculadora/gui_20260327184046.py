import sys
import os


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
        init_tcl = os.path.join(tcl_dir, "init.tcl")
        tk_tcl = os.path.join(tk_dir, "tk.tcl")

        if os.path.isfile(init_tcl):
            os.environ.setdefault("TCL_LIBRARY", tcl_dir)
        if os.path.isfile(tk_tcl):
            os.environ.setdefault("TK_LIBRARY", tk_dir)

        if os.environ.get("TCL_LIBRARY") and os.environ.get("TK_LIBRARY"):
            return


_bootstrap_tk_libraries()

import tkinter as tk
from tkinter import ttk

from conversor import ConversionError, convertir


class CalculadoraConversorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Sistemas Numericos")
        self.root.geometry("620x380")
        self.root.minsize(540, 320)

        self.numero_var = tk.StringVar()
        self.base_origen_var = tk.IntVar(value=10)
        self.base_destino_var = tk.IntVar(value=2)
        self.precision_var = tk.IntVar(value=12)
        self.resultado_var = tk.StringVar(value="")
        self.estado_var = tk.StringVar(value="Listo.")

        self._construir_ui()

    def _construir_ui(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        cabecera = ttk.Label(
            main,
            text="Conversor de Bases (2 a 36)",
            font=("Segoe UI", 14, "bold"),
        )
        cabecera.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        entrada_frame = ttk.LabelFrame(main, text="Entrada", padding=10)
        entrada_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        entrada_frame.columnconfigure(1, weight=1)

        ttk.Label(entrada_frame, text="Numero:").grid(row=0, column=0, sticky="w", pady=4)
        numero_entry = ttk.Entry(entrada_frame, textvariable=self.numero_var)
        numero_entry.grid(row=0, column=1, columnspan=3, sticky="ew", padx=(10, 0), pady=4)

        ttk.Label(entrada_frame, text="Base origen:").grid(row=1, column=0, sticky="w", pady=4)
        base_origen_combo = ttk.Combobox(
            entrada_frame,
            textvariable=self.base_origen_var,
            values=list(range(2, 37)),
            state="readonly",
            width=10,
        )
        base_origen_combo.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(entrada_frame, text="Base destino:").grid(row=1, column=2, sticky="w", pady=4, padx=(10, 0))
        base_destino_combo = ttk.Combobox(
            entrada_frame,
            textvariable=self.base_destino_var,
            values=list(range(2, 37)),
            state="readonly",
            width=10,
        )
        base_destino_combo.grid(row=1, column=3, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(entrada_frame, text="Precision decimal:").grid(row=2, column=0, sticky="w", pady=4)
        precision_spin = ttk.Spinbox(
            entrada_frame,
            from_=0,
            to=32,
            textvariable=self.precision_var,
            width=12,
        )
        precision_spin.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)

        botones = ttk.Frame(main)
        botones.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 8))
        botones.columnconfigure(0, weight=1)
        botones.columnconfigure(1, weight=1)
        botones.columnconfigure(2, weight=1)

        ttk.Button(botones, text="Convertir", command=self.convertir).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(botones, text="Intercambiar bases", command=self.intercambiar_bases).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(botones, text="Limpiar", command=self.limpiar).grid(row=0, column=2, sticky="ew", padx=(4, 0))

        salida_frame = ttk.LabelFrame(main, text="Resultado", padding=10)
        salida_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        salida_frame.columnconfigure(0, weight=1)

        resultado_entry = ttk.Entry(
            salida_frame,
            textvariable=self.resultado_var,
            state="readonly",
            font=("Consolas", 12, "bold"),
        )
        resultado_entry.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            salida_frame,
            text="Tip: usa letras A-Z para bases mayores a 10.",
            foreground="#666666",
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        estado = ttk.Label(main, textvariable=self.estado_var, foreground="#666666")
        estado.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.root.bind("<Return>", lambda _e: self.convertir())
        numero_entry.focus_set()

    def convertir(self):
        try:
            resultado = convertir(
                self.numero_var.get(),
                self.base_origen_var.get(),
                self.base_destino_var.get(),
                precision=self.precision_var.get(),
            )
        except ConversionError as exc:
            self.resultado_var.set("")
            self.estado_var.set(f"Error: {exc}")
            return

        self.resultado_var.set(resultado)
        self.estado_var.set("Conversion completada.")

    def intercambiar_bases(self):
        origen = self.base_origen_var.get()
        destino = self.base_destino_var.get()
        self.base_origen_var.set(destino)
        self.base_destino_var.set(origen)
        self.estado_var.set("Bases intercambiadas.")

    def limpiar(self):
        self.numero_var.set("")
        self.resultado_var.set("")
        self.estado_var.set("Listo.")


def main():
    root = tk.Tk()
    CalculadoraConversorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
