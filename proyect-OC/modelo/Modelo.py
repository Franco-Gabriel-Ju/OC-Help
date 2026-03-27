from modelo.Von_Neumann import VonNeuman


class Ejecutador:
    def __init__(self, modelo, instrucciones):
        self.cpu = modelo
        self.instrucciones = instrucciones

        self.dispatch = {
            "ROL_F_ACC": self.cpu.ROL_F_ACC,
            "ROR_F_ACC": self.cpu.ROR_F_ACC,
            "NOT_ACC": self.cpu.NOT_ACC,
            "NOT_F": self.cpu.NOT_F,
            "INC_ACC": self.cpu.INC_ACC,
            "INC_GPR": self.cpu.INC_GPR,
            "ACC_TO_GPR": self.cpu.ACC_TO_GPR,
            "GPR_TO_ACC": self.cpu.GPR_TO_ACC,
            "SUM_ACC_GPR": self.cpu.SUM_ACC_GPR,
            "ZERO_ACC": self.cpu.ZERO_TO_ACC,
            "ZERO_F": self.cpu.ZERO_TO_F,
            "GPR_AD_TO_MAR": self.cpu.GPR_AD_TO_MAR,
            "GPR_TO_M": self.cpu.GPR_TO_M,
            "M_TO_GPR": self.cpu.M_TO_GPR,
        }

    def ejecutar_instruccion(self, i):
        if i < 0 or i >= len(self.instrucciones):
            raise IndexError("Índice de instrucción fuera de rango")

        instr = self.instrucciones[i]
        nombre = instr[0]

        if nombre in self.dispatch:
            self.dispatch[nombre]()
        else:
            raise Exception(f"Instrucción desconocida: {nombre}")