import tkinter as tk
from tkinter import ttk

class CPU_UI:

    def __init__(self, root):
        self.root = root
        self.configurar_ventana()

        # Variables globales
        self.mem_vars_edit = []
        self.mem_vars_view = []

        # Layout principal
        self.main = ttk.Frame(root, padding=8)
        self.main.pack(fill="both", expand=True)

        self.main.columnconfigure(0, weight=0)
        self.main.columnconfigure(1, weight=1)
        self.main.rowconfigure(0, weight=1)
        self.main.rowconfigure(1, weight=1)

        # Crear secciones
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
            "MAR": tk.StringVar(value="000000000000"),
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

        # Widget de números de línea
        self.line_numbers = tk.Text(editor_frame, width=4, padx=4, takefocus=0,
                                border=0, background="lightgray", state="disabled")
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        # Editor principal
        self.code = tk.Text(editor_frame, font=("Courier", 10))
        self.code.grid(row=0, column=1, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=self._on_scroll)
        scrollbar.grid(row=0, column=2, sticky="ns")

        self.code.config(yscrollcommand=scrollbar.set)

        # Eventos para actualizar líneas
        self.code.bind("<KeyRelease>", self.actualizar_lineas)
        self.code.bind("<MouseWheel>", self.actualizar_lineas)
        self.code.bind("<Button-1>", self.actualizar_lineas)

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

    def crear_resultados(self, parent):
        results = ttk.LabelFrame(parent, text="Resultados", padding=10)
        results.grid(row=0, column=0, sticky="nsew", padx=(0,5))

        self.result_labels = {}

        for name in ["ACC","GPR","MAR","M"]:
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
    # 🧩 Memoria (Reusable)
    # ---------------------------
    def create_memory(self, parent, editable=False):
        canvas = tk.Canvas(parent, width=180, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        vars_list = []

        for i in range(256):
            addr = f"{i:04X}"
            var = tk.StringVar(value="000000000000")
            vars_list.append(var)

            row = ttk.Frame(inner)
            row.pack(anchor="w", fill="x")

            ttk.Label(row, text=addr, width=6).pack(side="left")

            if editable:
                ttk.Entry(row, textvariable=var, width=15).pack(side="left", padx=2)
            else:
                ttk.Label(row, textvariable=var, width=15, background="white").pack(side="left", padx=2)

        return vars_list


# ---------------------------
# 🚀 MAIN
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CPU_UI(root)
    root.mainloop()