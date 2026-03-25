import tkinter as tk
from tkinter import ttk

class CPU_UI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador CPU")

        # ====== CONTENEDOR PRINCIPAL ======
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # ====== TOP (REGISTROS + CODIGO) ======
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="both", expand=True)

        # ====== IZQUIERDA: REGISTROS ======
        reg_frame = ttk.LabelFrame(top_frame, text="Registros", padding=10)
        reg_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.registers = {
            "ACC": tk.StringVar(value="000000000000"),
            "GPR": tk.StringVar(value="000000000000"),
            "F": tk.StringVar(value="0"),
            "MAR": tk.StringVar(value="000000000000"),
            "M": tk.StringVar(value="000000000000"),
        }

        for i, (reg, var) in enumerate(self.registers.items()):
            ttk.Label(reg_frame, text=reg).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(reg_frame, textvariable=var, width=20).grid(row=i, column=1, pady=2)

        # ====== DERECHA: EDITOR ======
        code_frame = ttk.LabelFrame(top_frame, text="Editor de Código", padding=10)
        code_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.code_text = tk.Text(code_frame, wrap="none", font=("Courier", 10))
        self.code_text.pack(fill="both", expand=True)

        # ====== BOTTOM: MEMORIA ======
        mem_frame = ttk.LabelFrame(main_frame, text="Memoria RAM", padding=10)
        mem_frame.pack(fill="both", expand=True, padx=5, pady=5)

        canvas = tk.Canvas(mem_frame)
        scrollbar = ttk.Scrollbar(mem_frame, orient="vertical", command=canvas.yview)

        self.mem_inner = ttk.Frame(canvas)

        self.mem_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.mem_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ====== CREAR MEMORIA ======
        self.memory_labels = []
        for i in range(256):  # podés aumentar
            addr = f"{i:04X}"
            value = "000000000000"

            frame = ttk.Frame(self.mem_inner)
            frame.grid(row=i, column=0, sticky="w", pady=1)

            ttk.Label(frame, text=addr, width=6).pack(side="left")
            val_label = ttk.Label(frame, text=value, width=16)
            val_label.pack(side="left")

            self.memory_labels.append(val_label)


if __name__ == "__main__":
    root = tk.Tk()
    app = CPU_UI(root)
    root.mainloop()