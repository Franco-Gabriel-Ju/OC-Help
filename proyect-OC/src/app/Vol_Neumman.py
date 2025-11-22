from bitstring import BitArray

class Memoria:
    def __init__(self, size=1024):
        """
        Inicializa la memoria RAM simulada.
        size: número de palabras de 12 bits.
        """
        self.size = size
        # Cada palabra es un BitArray de 12 bits inicializado en 0
        self.ram = [BitArray(uint=0, length=12) for _ in range(size)]

    def leer(self, direccion):
        """
        Devuelve el contenido de la dirección de memoria.
        """
        if 0 <= direccion < self.size:
            return self.ram[direccion]
        else:
            raise IndexError("Dirección de memoria fuera de rango")

    def escribir(self, direccion, valor):
        """
        Escribe un valor de 12 bits en la dirección especificada.
        """
        if 0 <= direccion < self.size:
            # & 0xFFF asegura que el valor sea de 12 bits
            self.ram[direccion] = BitArray(uint=valor & 0xFFF, length=12)
        else:
            raise IndexError("Dirección de memoria fuera de rango, direccion invalida")

    def dump(self):
        """
        Devuelve toda la memoria en formato binario para inspección.
        """
        return [palabra.bin for palabra in self.ram]

class VonNeuman:
    def __init__(self):
        # Registros públicos (usar directamente cpu.ACC, cpu.F, ...)
        self.ACC = BitArray(uint=0, length=12)   # Acumulador (12 bits)
        self.F   = BitArray(uint=0, length=1)    # Flag de overflow (1 bit)
        self.GPR = BitArray(uint=0, length=12)   # Registro general (12 bits)
        self.M   = BitArray(uint=0, length=12)   # Registro de memoria (12 bits)
        self.RAM = Memoria()                     # RAM: instancia de Memoria (array de BitArray)

    # Nota: quitadas las funciones get_/set_. Usar los atributos públicos: ACC, F, GPR, M, RAM

    def ROL_F_ACC(self):
        concatenacion = self.F + self.ACC
        concatenacion.rol(1)
        # concatenacion[0] es un bool -> convertir a BitArray de 1 bit
        self.F = BitArray([concatenacion[0]])
        self.ACC = concatenacion[1:]
    
    def ROR_F_ACC(self):
        concatenacion = self.F + self.ACC
        concatenacion.ror(1)
        self.F = BitArray([concatenacion[0]])
        self.ACC = concatenacion[1:]
    
    def NOT_ACC(self):
        self.ACC = ~self.ACC
    
    def ACC_incrementar_a_ACC(self):
        suma = (self.ACC.uint + 1) & 0xFFF
        self.ACC = BitArray(uint=suma, length=12)
    
    def ACC_a_GPR(self):
        self.GPR = self.ACC.copy()

    def GPR_a_ACC(self):
        self.ACC = self.GPR.copy()
    
    def ACC_suma_GPR(self):
        suma = self.ACC.uint + self.GPR.uint
        if suma > 0xFFF:
            self.F = BitArray(uint=1, length=1)  # overflow
        else:
            self.F = BitArray(uint=0, length=1)
        
        self.ACC = BitArray(uint=suma & 0xFFF, length=12)
    


# PRUEBAS
"""
cpu = VonNeuman()

def inicializar_cpu(acc=12, f=1, gpr=3, m=0):
    cpu.ACC = BitArray(uint=acc & 0xFFF, length=12)
    cpu.F = BitArray(uint=f & 0x1, length=1)
    cpu.GPR = BitArray(uint=gpr & 0xFFF, length=12)
    cpu.M = BitArray(uint=m & 0xFFF, length=12)


def mostrar_estado(etiqueta):
    print(etiqueta)
    print("ACC:", cpu.ACC.bin)
    print("F  :", cpu.F.bin)
    print("GPR:", cpu.GPR.bin)
    print("M  :", cpu.M.bin)
    print()

mostrar_estado("Estado inicial:")

# Incrementar ACC
cpu.ACC_incrementar_a_ACC()
mostrar_estado("Después de ACC_incrementar_a_ACC():")

# NOT en ACC
cpu.NOT_ACC()
mostrar_estado("Después de NOT_ACC():")

# ROL con F
cpu.ROL_F_ACC()
mostrar_estado("Después de ROL_F_ACC():")

# ROR con F
cpu.ROR_F_ACC()
mostrar_estado("Después de ROR_F_ACC():")

# Copiar ACC a GPR
cpu.ACC_a_GPR()
mostrar_estado("Después de ACC_a_GPR():")

# Cambiar ACC y copiar desde GPR
cpu.ACC_incrementar_a_ACC()
cpu.GPR_a_ACC()
mostrar_estado("Después de GPR_a_ACC():")

"""