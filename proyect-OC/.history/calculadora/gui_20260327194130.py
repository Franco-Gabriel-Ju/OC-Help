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
        self.root.title("Calculadora y Asistente de Conversion")
        self.root.geometry("900x620")
        self.root.minsize(760, 560)

        self.numero_var = tk.StringVar()
        self.base_origen_var = tk.IntVar(value=10)
        self.base_destino_var = tk.IntVar(value=2)
        self.precision_var = tk.IntVar(value=12)
        self.complemento_var = tk.StringVar(value="ninguno")
        self.bits_complemento_var = tk.IntVar(value=16)
        self.separador_var = tk.StringVar(value=".")
        self.resultado_var = tk.StringVar(value="")
        self.estado_var = tk.StringVar(value="Listo.")
        self.resumen_var = tk.StringVar(value="Configuracion: base 10 -> base 2 | sin complemento")
        self.plantilla_var = tk.StringVar(value="Personalizado")

        self._construir_ui()
        self._actualizar_resumen()
        self._toggle_bits_state()

        self.base_origen_var.trace_add("write", lambda *_: self._actualizar_resumen())
        self.base_destino_var.trace_add("write", lambda *_: self._actualizar_resumen())
        self.precision_var.trace_add("write", lambda *_: self._actualizar_resumen())
        self.complemento_var.trace_add("write", lambda *_: self._on_complemento_change())
        self.separador_var.trace_add("write", lambda *_: self._actualizar_resumen())

    def _construir_ui(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("Main.TFrame", background="#f4f6fb")
        style.configure("Hero.TFrame", background="#1f3a5f")
        style.configure("HeroTitle.TLabel", background="#1f3a5f", foreground="#ffffff", font=("Segoe UI Semibold", 17))
        style.configure("HeroSub.TLabel", background="#1f3a5f", foreground="#d7e6f8", font=("Segoe UI", 10))
        style.configure("Result.TEntry", font=("Consolas", 15, "bold"))
        style.configure("Hint.TLabel", foreground="#5b6470")
        style.configure("Accent.TButton", font=("Segoe UI Semibold", 10))

        main = ttk.Frame(self.root, padding=0, style="Main.TFrame")
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)

        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        hero = ttk.Frame(main, style="Hero.TFrame", padding=(18, 16))
        hero.grid(row=0, column=0, sticky="ew")
        hero.columnconfigure(0, weight=1)

        ttk.Label(hero, text="Calculadora de Conversion y Complemento", style="HeroTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero,
            text="Modo rapido para convertir y modo cuestionario para ejercicios tipicos.",
            style="HeroSub.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        body = ttk.Frame(main, padding=14, style="Main.TFrame")
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        resumen_box = ttk.Frame(body, padding=(10, 8))
        resumen_box.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        resumen_box.columnconfigure(0, weight=1)

        ttk.Label(resumen_box, textvariable=self.resumen_var, style="Hint.TLabel").grid(row=0, column=0, sticky="w")

        notebook = ttk.Notebook(body)
        notebook.grid(row=1, column=0, sticky="nsew")

        tab_rapido = ttk.Frame(notebook, padding=14)
        tab_cuestionario = ttk.Frame(notebook, padding=14)
        notebook.add(tab_rapido, text="Conversion Rapida")
        notebook.add(tab_cuestionario, text="Modo Cuestionario")

        self._construir_tab_conversion(tab_rapido)
        self._construir_tab_cuestionario(tab_cuestionario)

        footer = ttk.Frame(body)
        footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.estado_var, style="Hint.TLabel").grid(row=0, column=0, sticky="w")

        self.root.bind("<Return>", lambda _e: self.convertir())

    def _construir_tab_conversion(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)

        entrada_frame = ttk.LabelFrame(parent, text="1) Ingresa tu numero", padding=10)
        entrada_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        entrada_frame.columnconfigure(1, weight=1)

        ttk.Label(entrada_frame, text="Numero (acepta . o ,):").grid(row=0, column=0, sticky="w", pady=4)
        self.numero_entry = ttk.Entry(entrada_frame, textvariable=self.numero_var, font=("Consolas", 12))
        self.numero_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

        formato_bar = ttk.Frame(entrada_frame)
        formato_bar.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 2))
        ttk.Button(formato_bar, text="Insertar -", command=lambda: self._append_numero("-")).grid(row=0, column=0, padx=(0, 4))
        ttk.Button(formato_bar, text="Insertar A-F", command=lambda: self._append_numero("A")).grid(row=0, column=1, padx=4)
        ttk.Button(formato_bar, text=".", command=lambda: self._append_numero(".")).grid(row=0, column=2, padx=4)
        ttk.Button(formato_bar, text=",", command=lambda: self._append_numero(",")).grid(row=0, column=3, padx=4)
        ttk.Button(formato_bar, text="Borrar", command=self._retroceso_numero).grid(row=0, column=4, padx=4)
        ttk.Button(formato_bar, text="Limpiar", command=self.limpiar).grid(row=0, column=5, padx=4)

        config_frame = ttk.LabelFrame(parent, text="2) Configura conversion", padding=10)
        config_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0), padx=(0, 5))
        config_frame.columnconfigure(1, weight=1)

        ttk.Label(config_frame, text="Base origen:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(
            config_frame,
            textvariable=self.base_origen_var,
            values=list(range(2, 37)),
            state="readonly",
            width=10,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(config_frame, text="Base destino:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(
            config_frame,
            textvariable=self.base_destino_var,
            values=list(range(2, 37)),
            state="readonly",
            width=10,
        ).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(config_frame, text="Precision fraccionaria:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Spinbox(
            config_frame,
            from_=0,
            to=32,
            textvariable=self.precision_var,
            width=12,
        ).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(config_frame, text="Separador:").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Combobox(
            config_frame,
            textvariable=self.separador_var,
            values=[".", ","],
            state="readonly",
            width=10,
        ).grid(row=3, column=1, sticky="w", padx=(10, 0), pady=4)

        comp_frame = ttk.LabelFrame(parent, text="3) Complemento (opcional)", padding=10)
        comp_frame.grid(row=1, column=1, sticky="nsew", pady=(10, 0), padx=(5, 0))
        comp_frame.columnconfigure(1, weight=1)

        ttk.Label(comp_frame, text="Tipo:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(
            comp_frame,
            textvariable=self.complemento_var,
            values=["ninguno", "a_uno", "a_dos"],
            state="readonly",
            width=12,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(comp_frame, text="Bits (solo binario):").grid(row=1, column=0, sticky="w", pady=4)
        self.bits_spin = ttk.Spinbox(
            comp_frame,
            from_=8,
            to=128,
            textvariable=self.bits_complemento_var,
            width=12,
        )
        self.bits_spin.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(
            comp_frame,
            text="Si no es base 2, se aplica mascara hibrida en la base destino.",
            style="Hint.TLabel",
            wraplength=280,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        acciones = ttk.Frame(parent)
        acciones.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        acciones.columnconfigure(0, weight=1)
        acciones.columnconfigure(1, weight=1)
        acciones.columnconfigure(2, weight=1)
        acciones.columnconfigure(3, weight=1)

        ttk.Button(acciones, text="Convertir", command=self.convertir, style="Accent.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(acciones, text="Intercambiar", command=self.intercambiar_bases).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(acciones, text="Copiar resultado", command=self._copiar_resultado).grid(row=0, column=2, sticky="ew", padx=4)
        ttk.Button(acciones, text="Limpiar", command=self.limpiar).grid(row=0, column=3, sticky="ew", padx=(4, 0))

        salida_frame = ttk.LabelFrame(parent, text="Resultado", padding=10)
        salida_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        salida_frame.columnconfigure(0, weight=1)

        self.resultado_entry = ttk.Entry(
            salida_frame,
            textvariable=self.resultado_var,
            state="readonly",
            style="Result.TEntry",
        )
        self.resultado_entry.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            salida_frame,
            text="Sin espacios. Si tu cuestionario pide coma, selecciona separador ','.",
            style="Hint.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.numero_entry.focus_set()

    def _construir_tab_cuestionario(self, parent):
        parent.columnconfigure(0, weight=1)

        bloque = ttk.LabelFrame(parent, text="Plantillas para preguntas frecuentes", padding=10)
        bloque.grid(row=0, column=0, sticky="ew")
        bloque.columnconfigure(1, weight=1)

        ttk.Label(bloque, text="Plantilla:").grid(row=0, column=0, sticky="w", pady=4)
        plantilla_combo = ttk.Combobox(
            bloque,
            textvariable=self.plantilla_var,
            values=[
                "Personalizado",
                "Binario en complemento (4 cifras)",
                "Octal en complemento",
                "Conversion simple con signo",
            ],
            state="readonly",
            width=38,
        )
        plantilla_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)
        plantilla_combo.bind("<<ComboboxSelected>>", self._aplicar_plantilla)

        ttk.Label(
            bloque,
            text=(
                "Tip de uso:\n"
                "1) Elegi plantilla.\n"
                "2) Ingresa numero y base origen.\n"
                "3) Presiona Convertir en la pestana Conversion Rapida."
            ),
            style="Hint.TLabel",
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

        ejemplos = ttk.LabelFrame(parent, text="Ejemplos de formato esperado", padding=10)
        ejemplos.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        ttk.Label(ejemplos, text="-E69,4BC -> binario en complemento, 4 cifras", style="Hint.TLabel").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(ejemplos, text="-FE,54 -> octal en complemento", style="Hint.TLabel").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(ejemplos, text="+BE33,EDA -> base 8 con signo explicito", style="Hint.TLabel").grid(row=2, column=0, sticky="w", pady=2)

    def _append_numero(self, token):
        actual = self.numero_var.get()
        if token == "A":
            self.numero_var.set(actual + "A")
            return
        self.numero_var.set(actual + token)

    def _retroceso_numero(self):
        actual = self.numero_var.get()
        self.numero_var.set(actual[:-1])

    def _aplicar_plantilla(self, _event=None):
        nombre = self.plantilla_var.get()

        if nombre == "Binario en complemento (4 cifras)":
            self.base_destino_var.set(2)
            self.complemento_var.set("a_dos")
            self.precision_var.set(4)
            self.separador_var.set(",")
            self.estado_var.set("Plantilla aplicada: binario en complemento con 4 cifras.")
        elif nombre == "Octal en complemento":
            self.base_destino_var.set(8)
            self.complemento_var.set("a_dos")
            self.precision_var.set(2)
            self.separador_var.set(",")
            self.estado_var.set("Plantilla aplicada: octal en complemento.")
        elif nombre == "Conversion simple con signo":
            self.complemento_var.set("ninguno")
            self.precision_var.set(3)
            self.separador_var.set(",")
            self.estado_var.set("Plantilla aplicada: conversion simple con signo.")
        else:
            self.estado_var.set("Plantilla personalizada.")

        self._actualizar_resumen()

    def _on_complemento_change(self):
        self._toggle_bits_state()
        self._actualizar_resumen()

    def _toggle_bits_state(self):
        if not hasattr(self, "bits_spin"):
            return
        if self.complemento_var.get() == "ninguno":
            self.bits_spin.state(["disabled"])
        else:
            self.bits_spin.state(["!disabled"])

    def _actualizar_resumen(self):
        comp = self.complemento_var.get()
        comp_texto = "sin complemento" if comp == "ninguno" else f"complemento {comp}"
        self.resumen_var.set(
            f"Configuracion: base {self.base_origen_var.get()} -> base {self.base_destino_var.get()} | "
            f"precision {self.precision_var.get()} | separador '{self.separador_var.get()}' | {comp_texto}"
        )

    def _copiar_resultado(self):
        valor = self.resultado_var.get().strip()
        if not valor:
            self.estado_var.set("No hay resultado para copiar.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(valor)
        self.estado_var.set("Resultado copiado al portapapeles.")

    def convertir(self):
        try:
            resultado = convertir(
                self.numero_var.get(),
                self.base_origen_var.get(),
                self.base_destino_var.get(),
                precision=self.precision_var.get(),
                complemento=self.complemento_var.get() if self.complemento_var.get() != "ninguno" else None,
                bits_complemento=self.bits_complemento_var.get(),
                separador=self.separador_var.get(),
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
