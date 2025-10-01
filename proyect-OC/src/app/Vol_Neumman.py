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
        self._ACC = BitArray(uint=0, length=12)   # Acumulador
        self._F   = BitArray(uint=0, length=1)    # Registro de sobrecarga
        self._GPR = BitArray(uint=0, length=12)   # Registro general
        self._M   = BitArray(uint=0, length=12)   # Registro de memoria
        self._RAM = BitArray(uint=0, length=12)   # RAM (ejemplo 1 palabra)

    # ------------------------
    # ACC
    def get_ACC(self):
        return self._ACC

    def set_ACC(self, valor):
        self._ACC = BitArray(uint=valor & 0xFFF, length=12)  # 12 bits

    # ------------------------
    # F (flag de sobrecarga)
    # ------------------------
    def get_F(self):
        return self._F

    def set_F(self, valor):
        self._F = BitArray(uint=valor & 0x1, length=1)       # 1 bit

    # ------------------------
    # GPR
    # ------------------------
    def get_GPR(self):
        return self._GPR

    def set_GPR(self, valor):
        self._GPR = BitArray(uint=valor & 0xFFF, length=12)

    # ------------------------
    # M (registro de memoria)
    # ------------------------
    def get_M(self):
        return self._M

    def set_M(self, valor):
        self._M = BitArray(uint=valor & 0xFFF, length=12)

    # ------------------------
    # RAM
    # ------------------------
    def get_RAM(self):
        return self._RAM

    def set_RAM(self, valor):
        self._RAM = BitArray(uint=valor & 0xFFF, length=12)
    

    def ROL_F_ACC(self):
        concatenacion = self._F + self._ACC
        concatenacion.rol(1)
        self.F = BitArray([concatenacion[0]])
        self._ACC = concatenacion[1:]
    
    def ROR_F_ACC(self):
        concatenacion = self.F + self._ACC
        concatenacion.ror(1)
        self.F = BitArray([concatenacion[0]])
        self._ACC = concatenacion[1:]
    
    def NOT_ACC(self):
        self._ACC = ~self._ACC
    
    def ACC_incrementar_a_ACC(self):
        suma = (self._ACC.uint + 1) & 0xFFF
        self._ACC = BitArray(uint=suma, length=12)
    
    def ACC_a_GPR(self):
        self._GPR = self._ACC.copy()

    def GPR_a_ACC(self):
        self._ACC = self._GPR.copy()
    
    def ACC_suma_GPR(self):
        suma = self._ACC.uint + self._GPR.uint
        if suma > 0xFFF:
            self.F = BitArray(uint=1, length=1)  # overflow
        else:
            self.F = BitArray(uint=0, length=1)
        
        self._ACC = BitArray(uint=suma & 0xFFF, length=12)
    


# PRUEBAS

cpu = VonNeuman()

def inicializar_cpu(acc=12, f=1, gpr=3, m=0):
    cpu.set_ACC(acc)
    cpu.set_F(f)
    cpu.set_GPR(gpr)
    cpu.set_M(m)


def mostrar_estado(etiqueta):
    print(etiqueta)
    print("ACC:", cpu.get_ACC().bin)
    print("F  :", cpu.get_F().bin)
    print("GPR:", cpu.get_GPR().bin)
    print("M  :", cpu.get_M().bin)
    print()

mostrar_estado("Estado inicial:")

# Incrementar ACC
cpu._ACC_incrementar_a_ACC()
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
cpu._ACC_a_GPR()
mostrar_estado("Después de ACC_a_GPR():")

# Cambiar ACC y copiar desde GPR
cpu._ACC_incrementar_a_ACC()
cpu.GPR_a_ACC()
mostrar_estado("Después de GPR_a_ACC():")

