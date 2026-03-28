import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from bitstring import BitArray
from modelo.Von_Neumann import VonNeuman
from modelo import Inferidor
from modelo.Generador import generar, ErrorGeneracion
from compilador.AnalizadorSintactico import parser  # IMPORTANTE (arriba del archivo)
from config import PreferencesManager


class CPU_UI:

    def __init__(self, root):
        self.root = root
        self.prefs = PreferencesManager()
        self._theme_mode = self.prefs.get("theme", "mode")
        self._theme_colors = {}
        self._status_label = None
        self._instruccion_label = None
        self.configurar_ventana()
        self.crear_menubar()
        self.cpu = VonNeuman()
        self.pc = 0  # program counter

        self.mem_vars_edit = []
        self.mem_vars_view = []

        self.main = ttk.Frame(root, padding=8)
        self.main.pack(fill="both", expand=True)

        self.main.columnconfigure(0, weight=0)
        self.main.columnconfigure(1, weight=1)
        self.main.rowconfigure(0, weight=1)
        self.main.rowconfigure(1, weight=1)

        self.crear_barra_izquierda()
        self.crear_editor_codigo()
        self.crear_barra_inferior()

    # ---------------------------
    # 🪟 Ventana
    # ---------------------------
    def configurar_ventana(self):
        self.root.title("Simulador CPU")
        self.root.geometry("1100x700")

    def crear_menubar(self):
        menubar = tk.Menu(self.root)

        menu_archivo = tk.Menu(menubar, tearoff=0)
        menu_archivo.add_command(label="Reiniciar", command=self.reiniciar)
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir", command=self.root.destroy)

        menu_editar = tk.Menu(menubar, tearoff=0)
        menu_editar.add_command(label="Copiar", command=lambda: self.root.focus_get().event_generate("<<Copy>>"))
        menu_editar.add_command(label="Cortar", command=lambda: self.root.focus_get().event_generate("<<Cut>>"))
        menu_editar.add_command(label="Pegar", command=lambda: self.root.focus_get().event_generate("<<Paste>>"))
        menu_editar.add_separator()
        menu_editar.add_command(label="Preferencias", command=self.abrir_preferencias)

        menu_ver = tk.Menu(menubar, tearoff=0)
        menu_ver.add_command(label="Tema claro", command=lambda: self._set_theme_from_menu("light"))
        menu_ver.add_command(label="Tema oscuro", command=lambda: self._set_theme_from_menu("dark"))

        menu_ejecutar = tk.Menu(menubar, tearoff=0)
        menu_ejecutar.add_command(label="Ejecutar 1 instruccion", command=self.ejecutar_una)
        menu_ejecutar.add_command(label="Inferir instruccion", command=self.inferir_instruccion)
        menu_ejecutar.add_command(label="Generar microoperaciones", command=self.generar_microops)

        menu_ayuda = tk.Menu(menubar, tearoff=0)
        menu_ayuda.add_command(label="Acerca de", command=self.mostrar_acerca_de)

        menubar.add_cascade(label="Archivo", menu=menu_archivo)
        menubar.add_cascade(label="Editar", menu=menu_editar)
        menubar.add_cascade(label="Ver", menu=menu_ver)
        menubar.add_cascade(label="Ejecutar", menu=menu_ejecutar)
        menubar.add_cascade(label="Ayuda", menu=menu_ayuda)

        self.root.config(menu=menubar)
        self.menubar = menubar

    # ---------------------------
    # 📚 Barra Izquierda
    # ---------------------------
    def crear_barra_izquierda(self):
        left_panel = ttk.Frame(self.main)
        left_panel.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0,8))

        self.crear_registros(left_panel)
        self.crear_memoria_editable(left_panel)

    def crear_registros(self, parent):
        reg_frame = ttk.LabelFrame(parent, text="Registros", padding=10)
        reg_frame.pack(fill="x", anchor="nw", pady=(0, 5))

        self.registers = {
            "ACC": tk.StringVar(value="000000000000"),
            "GPR": tk.StringVar(value="000000000000"),
            "F": tk.StringVar(value="0"),
            "M": tk.StringVar(value="000000000000"),
        }

        for i, (name, var) in enumerate(self.registers.items()):
            ttk.Label(reg_frame, text=name, width=4).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(reg_frame, textvariable=var, width=16).grid(row=i, column=1, pady=2)

    def crear_memoria_editable(self, parent):
        frame = ttk.LabelFrame(parent, text="Memoria RAM", padding=8)
        frame.pack(fill="both", expand=True, pady=5)

        self.mem_vars_edit = self.create_memory(frame, editable=True)

    # ---------------------------
    # 🧠 Editor de Código
    # ---------------------------
    def crear_editor_codigo(self):
        editor_frame = ttk.LabelFrame(self.main, text="Editor de Código", padding=6)
        editor_frame.grid(row=0, column=1, sticky="nsew")

        editor_frame.columnconfigure(1, weight=1)
        editor_frame.rowconfigure(0, weight=1)

        font_family = self.prefs.get("editor", "font_family")
        font_size = self.prefs.get("editor", "font_size")

        self._line_number_bg = "lightgray"

        self.line_numbers = tk.Text(editor_frame, width=4, padx=4, takefocus=0,
                                   border=0, background=self._line_number_bg,
                                   fg="#000000", state="disabled",
                                   font=(font_family, font_size))
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        self.code = tk.Text(editor_frame, font=(font_family, font_size), bg="#ffffff", fg="#000000",
                            insertbackground="#000000")
        self.code.grid(row=0, column=1, sticky="nsew")

        scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=self._on_scroll)
        scrollbar.grid(row=0, column=2, sticky="ns")

        self.code.config(yscrollcommand=scrollbar.set)

        # Popup de autocompletado
        self.autocomplete_popup = tk.Toplevel(self.root)
        self.autocomplete_popup.withdraw()
        self.autocomplete_popup.overrideredirect(True)  # sin bordes de ventana
        self.autocomplete_popup.attributes("-topmost", True)

        self.autocomplete_list = tk.Listbox(
            self.autocomplete_popup,
            font=(font_family, font_size),
            height=6,
            selectbackground="#0078d7",
            selectforeground="white",
            bg="#f5f5f5",
            fg="#000000",
            bd=1,
            relief="solid"
        )
        self.autocomplete_list.pack(fill="both", expand=True)

        # Tooltip de descripción debajo del popup
        self.tooltip_var = tk.StringVar()
        self.tooltip_lbl = tk.Label(
            self.autocomplete_popup,
            textvariable=self.tooltip_var,
            font=(font_family, max(8, font_size - 2)),
            bg="#ffffcc",
            fg="#000000",
            anchor="w",
            padx=4
        )
        self.tooltip_lbl.pack(fill="x")

        self.autocomplete_list.bind("<ButtonRelease-1>", self.aplicar_autocompletado)
        self.autocomplete_list.bind("<Return>", self.aplicar_autocompletado)

        self.code.bind("<KeyRelease>", self._on_key_release)
        self.code.bind("<Tab>", self._on_tab)
        self.code.bind("<Escape>", lambda e: self.cerrar_autocomplete())
        self.code.bind("<Down>", self._mover_seleccion)
        self.code.bind("<Up>", self._mover_seleccion)
        self.code.bind("<FocusOut>", lambda e: self.cerrar_autocomplete())

        self.actualizar_lineas()
        self.aplicar_tema(self._theme_mode)

    # ---------------------------
    # Instrucciones disponibles para autocompletado
    # ---------------------------
    INSTRUCCIONES = [
        ("ACC+1 -> ACC",     "Incrementa ACC en 1"),
        ("GPR+1 -> GPR",     "Incrementa GPR en 1"),
        ("ACC+GPR -> ACC",   "Suma ACC + GPR, guarda en ACC"),
        ("GPR+ACC -> ACC",   "Suma GPR + ACC, guarda en ACC"),
        ("ACC -> GPR",       "Copia ACC a GPR"),
        ("GPR -> ACC",       "Copia GPR a ACC"),
        ("GPR -> M",         "Copia GPR al registro M"),
        ("M -> GPR",         "Copia M al registro GPR"),
        ("ACC! -> ACC",      "NOT de ACC (complemento a 1)"),
        ("! ACC",            "NOT de ACC (complemento a 1)"),
        ("! F",              "NOT del flag F"),
        ("0 -> ACC",         "Pone ACC en 0"),
        ("0 -> F",           "Pone F en 0"),
        ("ROL F, ACC",       "Rota izquierda F y ACC"),
        ("ROR F, ACC",       "Rota derecha F y ACC"),
        ("GPR(AD) -> MAR",   "GPR[dirección] -> registro MAR"),
        ("PC -> MAR",        "Copia PC al registro MAR (fetch)"),
        ("PC+1 -> PC",       "Incrementa el Program Counter"),
        ("GPR(OP) -> OPR",   "GPR[operador] -> registro OPR"),
    ]

    def _on_key_release(self, event=None):
        self.actualizar_lineas()
        # No mostrar autocomplete con teclas de navegación o modificadores
        if event and event.keysym in ("Up", "Down", "Left", "Right", "Return",
                                       "Tab", "Escape", "BackSpace", "Delete",
                                       "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return
        self.mostrar_autocomplete()

    def mostrar_autocomplete(self):
        # Obtener el texto de la línea actual hasta el cursor
        linea_actual = self.code.get("insert linestart", "insert")
        texto = linea_actual.lstrip()

        if len(texto) < 1:
            self.cerrar_autocomplete()
            return

        sugerencias = [
            (instr, desc) for instr, desc in self.INSTRUCCIONES
            if instr.lower().startswith(texto.lower())
        ]

        if not sugerencias:
            self.cerrar_autocomplete()
            return

        self.autocomplete_list.delete(0, "end")
        self._sugerencias_actuales = sugerencias
        for instr, _ in sugerencias:
            self.autocomplete_list.insert("end", instr)

        self.autocomplete_list.selection_set(0)
        self.tooltip_var.set(sugerencias[0][1])

        # Posicionar el popup debajo del cursor de texto
        bbox = self.code.bbox("insert")
        if not bbox:
            return
        x = self.code.winfo_rootx() + bbox[0]
        y = self.code.winfo_rooty() + bbox[1] + bbox[3]

        ancho = 280
        alto = min(len(sugerencias), 6) * 20 + 24
        self.autocomplete_popup.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.autocomplete_popup.deiconify()

    def cerrar_autocomplete(self):
        self.autocomplete_popup.withdraw()

    def aplicar_autocompletado(self, event=None):
        seleccion = self.autocomplete_list.curselection()
        if not seleccion:
            return
        instr, _ = self._sugerencias_actuales[seleccion[0]]
        # Reemplazar la línea actual completa con la instrucción seleccionada
        self.code.delete("insert linestart", "insert lineend")
        self.code.insert("insert linestart", instr)
        self.cerrar_autocomplete()
        self.code.focus_set()
        return "break"

    def _on_tab(self, event=None):
        if self.autocomplete_popup.winfo_viewable():
            return self.aplicar_autocompletado()
        # Tab normal: insertar espacios
        self.code.insert("insert", "    ")
        return "break"

    def _mover_seleccion(self, event=None):
        if not self.autocomplete_popup.winfo_viewable():
            return
        size = self.autocomplete_list.size()
        if size == 0:
            return
        cur = self.autocomplete_list.curselection()
        idx = cur[0] if cur else 0
        if event.keysym == "Down":
            idx = min(idx + 1, size - 1)
        elif event.keysym == "Up":
            idx = max(idx - 1, 0)
        self.autocomplete_list.selection_clear(0, "end")
        self.autocomplete_list.selection_set(idx)
        self.autocomplete_list.see(idx)
        if hasattr(self, "_sugerencias_actuales"):
            self.tooltip_var.set(self._sugerencias_actuales[idx][1])
        return "break"

    def actualizar_lineas(self, event=None):
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")

        line_count = int(self.code.index('end-1c').split('.')[0])

        for i in range(1, line_count + 1):
            self.line_numbers.insert("end", f"{i}\n")

        self.line_numbers.config(state="disabled")

    def _on_scroll(self, *args):
        self.code.yview(*args)
        self.line_numbers.yview(*args)

    # ---------------------------
    # 📊 Barra Inferior
    # ---------------------------
    def crear_barra_inferior(self):
        bottom = ttk.Frame(self.main)
        bottom.grid(row=1, column=1, sticky="nsew", pady=(6,0))

        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        bottom.rowconfigure(0, weight=1)

        self.crear_resultados(bottom)
        self.crear_memoria_visual(bottom)

        btn_frame = ttk.Frame(bottom)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        btn_frame.columnconfigure(2, weight=1)
        btn_frame.columnconfigure(3, weight=1)

        ejecutar_btn = ttk.Button(btn_frame, text="Ejecutar 1 instrucción", command=self.ejecutar_una)
        ejecutar_btn.grid(row=0, column=0, padx=4)

        reset_btn = ttk.Button(btn_frame, text="Reiniciar", command=self.reiniciar)
        reset_btn.grid(row=0, column=1, padx=4)

        inferir_btn = ttk.Button(btn_frame, text="Inferir instrucción", command=self.inferir_instruccion)
        inferir_btn.grid(row=0, column=2, padx=4)

        pref_btn = ttk.Button(btn_frame, text="Preferencias", command=self.abrir_preferencias)
        pref_btn.grid(row=0, column=3, padx=4)

        self.estado_var = tk.StringVar(value="Listo.")
        self._status_label = ttk.Label(bottom, textvariable=self.estado_var, anchor="w",
                           foreground="gray", font=("Courier", 9))
        self._status_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4)

        self.instruccion_var = tk.StringVar(value="")
        self._instruccion_label = ttk.Label(bottom, textvariable=self.instruccion_var, anchor="w",
                            font=("Courier", 12, "bold"), foreground="blue")
        self._instruccion_label.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 4))

        # ── Panel generador: instrucción → microoperaciones ──────────
        gen_frame = ttk.LabelFrame(bottom, text="Generar microoperaciones", padding=6)
        gen_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 2))
        gen_frame.columnconfigure(0, weight=1)

        gen_input_frame = ttk.Frame(gen_frame)
        gen_input_frame.pack(fill="x")
        gen_input_frame.columnconfigure(0, weight=1)

        ttk.Label(gen_input_frame, text="Instrucción:").grid(row=0, column=0, sticky="w")

        self.gen_var = tk.StringVar()
        gen_entry = ttk.Entry(gen_input_frame, textvariable=self.gen_var,
                              font=("Courier", 10), width=35)
        gen_entry.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        gen_entry.bind("<Return>", lambda e: self.generar_microops())

        gen_btn = ttk.Button(gen_input_frame, text="Generar", command=self.generar_microops)
        gen_btn.grid(row=1, column=1)

        ttk.Label(gen_input_frame,
                  text="Ej: ACC <- 8*ACC + 2  |  M <- 3*M - ACC  |  M <- -4*M",
                  foreground="gray", font=("Courier", 8)).grid(row=2, column=0, columnspan=2, sticky="w")

        self.gen_resultado_var = tk.StringVar(value="")
        gen_resultado_lbl = ttk.Label(gen_frame, textvariable=self.gen_resultado_var,
                                      font=("Courier", 9), foreground="darkgreen",
                                      anchor="w", justify="left")
        gen_resultado_lbl.pack(fill="x", pady=(4, 0))

    def crear_resultados(self, parent):
        results = ttk.LabelFrame(parent, text="Resultados", padding=10)
        results.grid(row=0, column=0, sticky="nsew", padx=(0,5))

        self.result_labels = {}

        for name in ["ACC","GPR","M"]:
            lbl = ttk.Label(results, text=f"{name}: 000000000000")
            lbl.pack(anchor="w", pady=2)
            self.result_labels[name] = lbl

        self.flag = ttk.Label(results, text="F: 0")
        self.flag.pack(anchor="w")

    def crear_memoria_visual(self, parent):
        frame = ttk.LabelFrame(parent, text="Memoria RAM", padding=8)
        frame.grid(row=0, column=1, sticky="nsew", padx=(5,0))

        self.mem_vars_view = self.create_memory(frame, editable=False)

    # ---------------------------
    # 🧩 Memoria
    # ---------------------------
    def create_memory(self, parent, editable=False):
        canvas = tk.Canvas(parent, width=180)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        vars_list = []

        for i in range(256):
            var = tk.StringVar(value="000000000000")
            vars_list.append(var)

            row = ttk.Frame(inner)
            row.pack(anchor="w")

            ttk.Label(row, text=f"{i:04X}", width=6).pack(side="left")

            if editable:
                ttk.Entry(row, textvariable=var, width=15).pack(side="left")
            else:
                ttk.Label(row, textvariable=var, width=15).pack(side="left")

        return vars_list

    # ---------------------------
    # 🔌 CONEXIÓN UI ↔ CPU
    # ---------------------------
    def cargar_memoria_desde_ui(self):
        for i, var in enumerate(self.mem_vars_edit):
            try:
                valor = int(var.get(), 2)
                self.cpu.RAM.escribir(i, valor)
            except:
                self.cpu.RAM.escribir(i, 0)

    def actualizar_memoria_ui(self):
        dump = self.cpu.RAM.dump()
        for i in range(len(dump)):
            self.mem_vars_view[i].set(dump[i])

    def cargar_registros_desde_ui(self):
        self.cpu.ACC = BitArray(bin=self.registers["ACC"].get())
        self.cpu.GPR = BitArray(bin=self.registers["GPR"].get())
        self.cpu.F   = BitArray(bin=self.registers["F"].get())
        self.cpu.M   = BitArray(bin=self.registers["M"].get())

    def actualizar_registros_ui(self):
        self.result_labels["ACC"].config(text=f"ACC: {self.cpu.ACC.bin}")
        self.result_labels["GPR"].config(text=f"GPR: {self.cpu.GPR.bin}")
        self.result_labels["M"].config(text=f"M: {self.cpu.M.bin}")
        self.flag.config(text=f"F: {self.cpu.F.bin}")

    # ---------------------------
    # ▶️ EJECUCIÓN
    # ---------------------------

    def ejecutar_una(self):
        if self.pc == 0:
            self.cargar_registros_desde_ui()
            self.cargar_memoria_desde_ui()

        lineas = self.code.get("1.0", "end").strip().split("\n")

        if self.pc >= len(lineas):
            self.mostrar_estado(f"Fin del programa — ACC={self.cpu.ACC.bin}", error=False)
            return

        linea = lineas[self.pc].strip()

        if not linea:
            self.pc += 1
            return

        instr = parser.parse(linea)

        if not instr or instr[0] is None:
            self.mostrar_estado(f"Línea {self.pc + 1}: error de sintaxis en '{linea}'", error=True)
            self.pc += 1
            return

        op = instr[0][0]

        dispatch = {
            "INC_ACC":      self.cpu.INC_ACC,
            "INC_GPR":      self.cpu.INC_GPR,
            "NOT_ACC":      self.cpu.NOT_ACC,
            "NOT_F":        self.cpu.NOT_F,
            "ROL_F_ACC":    self.cpu.ROL_F_ACC,
            "ROR_F_ACC":    self.cpu.ROR_F_ACC,
            "SUM_ACC_GPR":  self.cpu.SUM_ACC_GPR,
            "ACC_TO_GPR":   self.cpu.ACC_TO_GPR,
            "GPR_TO_ACC":   self.cpu.GPR_TO_ACC,
            "ZERO_ACC":     self.cpu.ZERO_TO_ACC,
            "ZERO_F":       self.cpu.ZERO_TO_F,
            "GPR_AD_TO_MAR":self.cpu.GPR_AD_TO_MAR,
            "GPR_TO_M":     self.cpu.GPR_TO_M,
            "M_TO_GPR":     self.cpu.M_TO_GPR,
            "PC_TO_MAR":    self.cpu.PC_TO_MAR,
            "INC_PC":       self.cpu.INC_PC,
            "GPR_OP_TO_OPR":self.cpu.GPR_OP_TO_OPR,
        }

        if op in dispatch:
            dispatch[op]()
            self.mostrar_estado(f"Línea {self.pc + 1}: {linea}  →  {op}", error=False)
        else:
            self.mostrar_estado(f"Línea {self.pc + 1}: instrucción no soportada '{op}'", error=True)

        self.pc += 1
        self.actualizar_registros_ui()
        self.actualizar_memoria_ui()

    def mostrar_estado(self, mensaje, error=False):
        self.estado_var.set(mensaje)
        color = "red" if error else "green"
        if self._status_label is not None:
            self._status_label.config(foreground=color)

    def abrir_preferencias(self):
        from preferences_dialog import PreferencesDialog

        dialog = PreferencesDialog(self.root, self.prefs, self.on_preferences_changed)
        self.root.wait_window(dialog)

    def on_preferences_changed(self):
        self._theme_mode = self.prefs.get("theme", "mode")
        font_family = self.prefs.get("editor", "font_family")
        font_size = self.prefs.get("editor", "font_size")

        self.code.config(font=(font_family, font_size))
        self.line_numbers.config(font=(font_family, font_size))
        self.autocomplete_list.config(font=(font_family, font_size))
        self.tooltip_lbl.config(font=(font_family, max(8, font_size - 2)))

        self.aplicar_tema(self._theme_mode)

    def aplicar_tema(self, mode):
        if mode == "dark":
            editor_bg = "#1e1e1e"
            editor_fg = "#d4d4d4"
            lines_bg = "#2f2f33"
            lines_fg = "#d4d4d4"
            popup_bg = "#252526"
            tooltip_bg = "#333333"
            tooltip_fg = "#f1f1f1"
            select_bg = "#0e639c"
        else:
            editor_bg = "#ffffff"
            editor_fg = "#000000"
            lines_bg = "lightgray"
            lines_fg = "#000000"
            popup_bg = "#f5f5f5"
            tooltip_bg = "#ffffcc"
            tooltip_fg = "#000000"
            select_bg = "#0078d7"

        self.code.config(bg=editor_bg, fg=editor_fg, insertbackground=editor_fg)
        self.line_numbers.config(background=lines_bg, fg=lines_fg)
        self.autocomplete_list.config(bg=popup_bg, fg=editor_fg, selectbackground=select_bg)
        self.tooltip_lbl.config(bg=tooltip_bg, fg=tooltip_fg)

    def inferir_instruccion(self):
        lineas = self.code.get("1.0", "end").strip().split("\n")
        ops = []
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
            instr = parser.parse(linea)
            if instr and instr[0] is not None:
                ops.append(instr[0][0])

        if not ops:
            self.instruccion_var.set("Sin instrucciones para inferir")
            return

        resultado = Inferidor.inferir(ops)
        self.instruccion_var.set(f"Instruccion: {resultado}")
        self.mostrar_estado(f"Inferencia completada ({len(ops)} operaciones)", error=False)

    def generar_microops(self):
        expresion = self.gen_var.get().strip()
        if not expresion:
            return
        try:
            ops = generar(expresion)
            # Insertar en el editor
            self.code.delete("1.0", "end")
            self.code.insert("1.0", "\n".join(ops))
            self.actualizar_lineas()
            self.gen_resultado_var.set(f"Generadas {len(ops)} instrucciones  →  cargadas en el editor")
            self.mostrar_estado(f"Generadas {len(ops)} ops para: {expresion}", error=False)
        except ErrorGeneracion as e:
            self.gen_resultado_var.set(f"Error: {e}")
            self.mostrar_estado("Error al generar", error=True)

    def reiniciar(self):
        self.pc = 0
        self.cpu = VonNeuman()
        for var in self.registers.values():
            var.set("000000000000" if len(var.get()) > 1 else "0")
        for var in self.mem_vars_edit:
            var.set("000000000000")
        for var in self.mem_vars_view:
            var.set("000000000000")
        self.actualizar_registros_ui()
        self.mostrar_estado("Reiniciado.", error=False)


def _base_proyecto():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ruta_logo():
    return os.path.join(_base_proyecto(), "images", "logo.png")


def _ruta_icono_app():
    return os.path.join(_base_proyecto(), "images", "LogoIconoGato.png")


def _cargar_icono_app():
    """
    Carga LogoIconoGato.png para barra de tareas y título (PNG, Tk 8.6+).
    Devuelve tk.PhotoImage o None.
    """
    try:
        ruta = _ruta_icono_app()
        if not os.path.isfile(ruta):
            return None
        img = tk.PhotoImage(file=ruta)
        wmax = 128
        while img.width() > wmax or img.height() > wmax:
            img = img.subsample(2, 2)
        return img
    except tk.TclError:
        return None


def _aplicar_icono_ventana(ventana, icono_foto, default=True):
    """Asocia el icono a la ventana; default=True aplica también a hijos (Toplevel)."""
    if icono_foto is None:
        return
    try:
        ventana.iconphoto(default, icono_foto)
        ventana._icono_app_photo = icono_foto
    except tk.TclError:
        pass


def mostrar_splash_y_luego(root, callback, icono_foto=None):
    """
    Muestra el logo sobre fondo blanco; al cerrar (clic o tiempo) ejecuta callback().
    """
    splash = tk.Toplevel(root)
    if icono_foto is not None:
        _aplicar_icono_ventana(splash, icono_foto, default=False)
    splash.overrideredirect(True)
    splash.configure(bg="white")
    splash.attributes("-topmost", True)

    img_ref = {"photo": None}
    hecho = {"ok": False}

    try:
        img_ref["photo"] = tk.PhotoImage(file=_ruta_logo())
        while img_ref["photo"].width() > 900:
            img_ref["photo"] = img_ref["photo"].subsample(2, 2)
        lbl = tk.Label(splash, image=img_ref["photo"], bg="white", bd=0)
    except tk.TclError:
        lbl = tk.Label(
            splash,
            text="DEVS PROJECT\nOC HELP",
            bg="white",
            fg="#1a237e",
            font=("Segoe UI", 22, "bold"),
            padx=48,
            pady=48,
        )

    lbl.pack()
    lbl.image = img_ref.get("photo")

    hint = tk.Label(
        splash,
        text="Clic o Enter para continuar",
        bg="white",
        fg="#888888",
        font=("Segoe UI", 9),
    )
    hint.pack(pady=(0, 12))

    splash.update_idletasks()
    w = splash.winfo_reqwidth()
    h = splash.winfo_reqheight()
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 2)
    splash.geometry(f"+{x}+{y}")

    timer_id = {"id": None}

    def cerrar(_event=None):
        if hecho["ok"]:
            return
        hecho["ok"] = True
        if timer_id["id"] is not None:
            try:
                splash.after_cancel(timer_id["id"])
            except tk.TclError:
                pass
        try:
            splash.destroy()
        except tk.TclError:
            pass
        callback()

    splash.bind("<Button-1>", cerrar)
    splash.bind("<Return>", cerrar)
    splash.bind("<Escape>", cerrar)
    timer_id["id"] = splash.after(4000, cerrar)


# ---------------------------
# 🚀 MAIN
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    _icono_app = _cargar_icono_app()
    _aplicar_icono_ventana(root, _icono_app, default=True)
    root.withdraw()

    def iniciar_app():
        app = CPU_UI(root)
        root.deiconify()
        root.lift()
        root.focus_force()

    mostrar_splash_y_luego(root, iniciar_app, icono_foto=_icono_app)
    root.mainloop()