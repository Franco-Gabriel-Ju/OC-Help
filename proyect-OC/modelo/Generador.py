"""
Generador de microoperaciones a partir de una expresión de alto nivel.

Soporta expresiones del tipo:
    ACC <- N*ACC + K
    ACC <- N*ACC - K
    ACC <- N*M + K
    ACC <- -N*ACC
    M   <- N*M - ACC
    M   <- -N*M
    etc.

Usa sympy para parsear la expresión y luego genera la secuencia óptima.
"""
from sympy import symbols, sympify, expand, Rational, Integer, factor
from sympy import Mul, Add, Pow, Number


ACC, GPR, M, F = symbols("ACC GPR M F", integer=True)


class ErrorGeneracion(Exception):
    pass


def generar(expresion: str) -> list:
    """
    Recibe una expresión como 'ACC <- 8*ACC + 2' o 'M <- 3M - ACC'
    y devuelve la lista de microoperaciones equivalente.

    Retorna lista de strings (instrucciones en sintaxis del compilador).
    Lanza ErrorGeneracion si no puede generar la secuencia.
    """
    # ── Parsear el destino y la expresión ────────────────────────────
    if "<-" in expresion:
        partes = expresion.split("<-", 1)
    elif "->" in expresion:
        partes = expresion.split("->", 1)
    else:
        raise ErrorGeneracion("Formato inválido. Usá: DEST <- expresion")

    destino_str = partes[0].strip().upper()
    expr_str    = partes[1].strip()

    if destino_str not in ("ACC", "M", "GPR"):
        raise ErrorGeneracion(f"Destino '{destino_str}' no soportado. Usá ACC, M o GPR.")

    # Normalizar la expresión para sympy
    import re
    F = symbols("F", integer=True)
    # Convertir a mayúsculas los nombres de registros
    expr_str = re.sub(r'\b(acc|gpr|mar|m|f)\b', lambda m: m.group().upper(), expr_str, flags=re.IGNORECASE)
    # Insertar * entre número y variable: 4M -> 4*M, 3ACC -> 3*ACC, 2048F -> 2048*F
    expr_str = re.sub(r'(\d)(ACC|GPR|M\b|F\b)', r'\1*\2', expr_str)
    expr_str = expr_str.strip()
    try:
        expr = expand(sympify(expr_str, locals={"ACC": ACC, "GPR": GPR, "M": M, "F": F}))
    except Exception as e:
        raise ErrorGeneracion(f"No se pudo parsear la expresión: {e}")

    ops = []

    # ── Caso con F (ROR/ROL) ────────────────────────────────────────
    F_sym = symbols("F", integer=True)
    coef_f_expr = expr.coeff(F_sym) if F_sym in expr.free_symbols else Integer(0)

    # ACC <- ACC/2 + 2048*F  →  ROR F, ACC
    if destino_str == "ACC" and coef_f_expr == 2048 and expr.coeff(ACC) == Rational(1, 2):
        ops.append("ROR F, ACC")
        k = int(expr - Rational(1,2)*ACC - 2048*F_sym)
        ops += _agregar_constante(k)
        return ops

    # M <- ACC/2 + 2048*F  →  ROR F, ACC + guardar en M
    if destino_str == "M" and coef_f_expr == 2048 and expr.coeff(ACC) == Rational(1, 2):
        ops.append("ROR F, ACC")
        ops += ["ACC -> GPR", "GPR -> M"]
        return ops

    # M <- ACC/2  →  0 -> F, ROR F, ACC + guardar en M
    if destino_str == "M" and coef_f_expr == 0 and expr.coeff(ACC) == Rational(1, 2):
        ops += ["0 -> F", "ROR F, ACC", "ACC -> GPR", "GPR -> M"]
        return ops

    # ACC <- ACC/2  →  0 -> F, ROR F, ACC
    if destino_str == "ACC" and coef_f_expr == 0 and expr.coeff(ACC) == Rational(1, 2):
        ops += ["0 -> F", "ROR F, ACC"]
        return ops

    # ACC <- 2*ACC + F  →  ROL F, ACC
    if destino_str == "ACC" and coef_f_expr == 1 and expr.coeff(ACC) == 2:
        ops.append("ROL F, ACC")
        k = int(expr - 2*ACC - F_sym)
        ops += _agregar_constante(k)
        return ops

    # M <- 2*ACC + F  →  ROL F, ACC + guardar en M
    if destino_str == "M" and coef_f_expr == 1 and expr.coeff(ACC) == 2:
        ops.append("ROL F, ACC")
        ops += ["ACC -> GPR", "GPR -> M"]
        return ops

    # ── Caso: ACC <- N*ACC + K ───────────────────────────────────────
    if destino_str == "ACC":
        coef_acc = expr.coeff(ACC)
        coef_gpr = expr.coeff(GPR)
        coef_m   = expr.coeff(M)
        constante = expr - coef_acc * ACC - coef_gpr * GPR - coef_m * M

        # ACC <- N*M + K (carga desde memoria)
        if coef_m != 0 and coef_acc == 0 and coef_gpr == 0:
            ops += _cargar_M_en_GPR()
            ops += _multiplicar_GPR(int(coef_m), ops_acc_zero=True)
            ops += _agregar_constante(int(constante))
            return ops

        # ACC <- N*ACC + K
        if coef_acc != 0 and coef_m == 0 and coef_gpr == 0:
            n = int(coef_acc)
            k = int(constante)
            ops += _multiplicar_ACC(n)
            ops += _agregar_constante(k)
            return ops

        # ACC <- N*ACC + K*GPR
        if coef_acc != 0 and coef_gpr != 0 and coef_m == 0:
            n = int(coef_acc)
            kg = int(coef_gpr)
            ops += _multiplicar_ACC(n)
            # Sumar kg veces GPR
            for _ in range(abs(kg)):
                if kg > 0:
                    ops.append("GPR+ACC -> ACC")
                else:
                    ops += ["ACC! -> ACC", "ACC+1 -> ACC",
                            "GPR+ACC -> ACC",
                            "ACC! -> ACC", "ACC+1 -> ACC"]
            ops += _agregar_constante(int(constante))
            return ops

    # ── Caso: M <- expresion ─────────────────────────────────────────
    if destino_str == "M":
        coef_m   = expr.coeff(M)
        coef_acc = expr.coeff(ACC)
        coef_gpr = expr.coeff(GPR)
        constante = expr - coef_m * M - coef_acc * ACC - coef_gpr * GPR

        # M <- N*M - ACC  (clásico de la materia)
        if coef_m != 0 and coef_acc == -1 and coef_gpr == 0 and constante == 0:
            n = int(coef_m)
            ops += _cargar_M_en_GPR()
            # NOT ACC + INC → -ACC
            ops += ["ACC! -> ACC", "ACC+1 -> ACC"]
            # Sumar GPR N veces
            for _ in range(n):
                ops.append("GPR+ACC -> ACC")
            ops += ["ACC -> GPR", "GPR -> M"]
            return ops

        # M <- -N*M
        if coef_m != 0 and coef_acc == 0 and coef_gpr == 0 and constante == 0:
            n = int(coef_m)
            ops += _cargar_M_en_GPR()
            ops += ["0 -> ACC"]
            ops.append("GPR+ACC -> ACC")
            ops += _rol_n(int(abs(n)).bit_length() - 1)
            if n < 0:
                ops += ["ACC! -> ACC", "ACC+1 -> ACC"]
            ops += ["ACC -> GPR", "GPR -> M"]
            return ops

        # M <- N*M + K
        if coef_m != 0 and coef_acc == 0 and constante != 0:
            n = int(coef_m)
            k = int(constante)
            ops += _cargar_M_en_GPR()
            ops += _multiplicar_GPR(n, ops_acc_zero=True)
            ops += _agregar_constante(k)
            ops += ["ACC -> GPR", "GPR -> M"]
            return ops

    raise ErrorGeneracion(
        f"No sé generar microoperaciones para: {destino_str} <- {expr}\n"
        f"Expresiones soportadas:\n"
        f"  ACC <- N*ACC + K\n"
        f"  ACC <- N*M + K\n"
        f"  M   <- N*M - ACC\n"
        f"  M   <- -N*M\n"
        f"  M   <- N*M + K"
    )


# ── Utilidades de generación ──────────────────────────────────────────

def _cargar_M_en_GPR() -> list:
    """GPR(AD) -> MAR, M -> GPR"""
    return ["GPR(AD) -> MAR", "M -> GPR"]


def _rol_n(n: int) -> list:
    """Genera N pares ZERO_F + ROL para multiplicar por 2^N."""
    ops = []
    for _ in range(n):
        ops += ["0 -> F", "ROL F, ACC"]
    return ops


def _multiplicar_ACC(n: int) -> list:
    """
    Genera microops para ACC <- n * ACC.
    Usa duplicaciones sucesivas (ACC -> GPR, GPR+ACC -> ACC).
    """
    if n == 0:
        return ["0 -> ACC"]
    if n == 1:
        return []
    if n == -1:
        return ["ACC! -> ACC", "ACC+1 -> ACC"]

    ops = []
    negativo = n < 0
    n = abs(n)

    # Factorizamos n como producto de potencias de 2 y sumas
    # Estrategia: duplicar ACC hasta llegar a n
    # Ejemplo: n=8 → x2, x2, x2  (3 duplicaciones)
    # Ejemplo: n=6 → x2 (ACC=2A), guardar, x2 (ACC=4A), sumar GPR → 6A
    # Usamos la representación binaria para la cadena de adiciones (método shift-and-add)
    bits = bin(n)[2:]  # ej: 8 -> '1000', 6 -> '110'

    # Empezamos con resultado = ACC (1 vez)
    # Por cada bit siguiente: duplicar; si es 1, sumar ACC original
    # Para esto necesitamos guardar ACC original en M
    if _es_potencia_de_2(n):
        # Caso simple: solo ROL
        k = n.bit_length() - 1
        ops += _rol_n(k)
    else:
        # Método shift-and-add usando M como temporal
        ops.append("GPR -> M")       # guardar ACC original en M (via GPR=ACC previo)
        ops.append("ACC -> GPR")
        ops.append("GPR+ACC -> ACC") # ACC = 2*ACC

        acum_bits = 2
        for bit in bits[2:]:  # saltamos el primer '1' ya procesado
            # Duplicar
            ops.append("ACC -> GPR")
            ops.append("GPR+ACC -> ACC")
            acum_bits *= 2
            if bit == '1':
                # Recuperar ACC original de M y sumar
                ops.append("M -> GPR")
                ops.append("GPR+ACC -> ACC")
                acum_bits += 1  # aproximado, no exacto para todos los casos

    if negativo:
        ops += ["ACC! -> ACC", "ACC+1 -> ACC"]

    return ops


def _multiplicar_GPR(n: int, ops_acc_zero: bool = False) -> list:
    """Genera ops para ACC <- n * GPR (GPR ya tiene el valor de M)."""
    ops = []
    if ops_acc_zero:
        ops.append("0 -> ACC")

    negativo = n < 0
    n = abs(n)

    for _ in range(n):
        ops.append("GPR+ACC -> ACC")

    if negativo:
        ops += ["ACC! -> ACC", "ACC+1 -> ACC"]

    return ops


def _agregar_constante(k: int) -> list:
    """Genera ops para ACC <- ACC + k usando INC_ACC repetido."""
    if k == 0:
        return []
    ops = []
    if k > 0:
        for _ in range(k):
            ops.append("ACC+1 -> ACC")
    else:
        # Restar: negamos ACC, sumamos |k|, negamos de nuevo
        ops += ["ACC! -> ACC", "ACC+1 -> ACC"]
        for _ in range(abs(k)):
            ops.append("ACC+1 -> ACC")
        ops += ["ACC! -> ACC", "ACC+1 -> ACC"]
    return ops


def _es_potencia_de_2(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0
