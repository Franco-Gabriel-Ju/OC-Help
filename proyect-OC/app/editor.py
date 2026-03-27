import tkinter as tk
from tkinter import ttk
from bitstring import BitArray
from modelo.Von_Neumann import VonNeuman
from compilador.AnalizadorSintactico import parser  # IMPORTANTE (arriba del archivo)


class CPU_UI:

    def __init__(self, root):
        self.root = root
        self.configurar_ventana()
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

        self.line_numbers = tk.Text(editor_frame, width=4, padx=4, takefocus=0,
                                   border=0, background="lightgray", state="disabled")
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        self.code = tk.Text(editor_frame, font=("Courier", 10))
        self.code.grid(row=0, column=1, sticky="nsew")

        scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=self._on_scroll)
        scrollbar.grid(row=0, column=2, sticky="ns")

        self.code.config(yscrollcommand=scrollbar.set)

        self.code.bind("<KeyRelease>", self.actualizar_lineas)
        self.actualizar_lineas()

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

        ejecutar_btn = ttk.Button(bottom, text="Ejecutar 1 instrucción", command=self.ejecutar_una)
        ejecutar_btn.grid(row=1, column=0, columnspan=2, pady=5)

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
            print(self.cpu.ACC.bin)
            print("Fin del programa")
            return

        linea = lineas[self.pc].strip()

        # 👉 parsear la línea
        instr = parser.parse(linea)

        print("LINEA:", linea)
        print("PARSE:", instr)

        if not instr:
            print("❌ Error de parsing")
            self.pc += 1
            return

        op = instr[0][0]
        print("Ejecutando:", op)

        # 🔥 SIN DISPATCH
        if op == "INC_ACC":
            self.cpu.INC_ACC()

        elif op == "INC_GPR":
            self.cpu.INC_GPR()

        elif op == "NOT_ACC":
            self.cpu.NOT_ACC()

        elif op == "NOT_F":
            self.cpu.NOT_F()

        elif op == "ROL_F_ACC":
            self.cpu.ROL_F_ACC()

        elif op == "ROR_F_ACC":
            self.cpu.ROR_F_ACC()

        elif op == "SUM_ACC_GPR":
            self.cpu.SUM_ACC_GPR()

        elif op == "ACC_TO_GPR":
            self.cpu.ACC_TO_GPR()

        elif op == "GPR_TO_ACC":
            self.cpu.GPR_TO_ACC()

        elif op == "ZERO_ACC":
            self.cpu.ZERO_TO_ACC()

        elif op == "ZERO_F":
            self.cpu.ZERO_TO_F()

        elif op == "GPR_AD_TO_MAR":
            self.cpu.GPR_AD_TO_MAR()

        elif op == "GPR_TO_M":
            self.cpu.GPR_TO_M()

        elif op == "M_TO_GPR":
            self.cpu.M_TO_GPR()

        else:
            print("❌ Instrucción no soportada:", op)

        self.pc += 1

        self.actualizar_registros_ui()
        self.actualizar_memoria_ui()
  


# ---------------------------
# 🚀 MAIN
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CPU_UI(root)
    root.mainloop()