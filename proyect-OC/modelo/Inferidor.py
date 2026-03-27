"""
Inferidor de instrucciones de alto nivel mediante ejecución simbólica.

En vez de hardcodear patrones, simula cada operación usando variables
simbólicas (sympy). Al final muestra qué expresión matemática quedó
en cada registro modificado.
"""
from sympy import symbols, simplify, factor, Not, Symbol
from sympy import Rational, Integer


# Símbolos iniciales para cada registro
ACC0, GPR0, M0, F0 = symbols("ACC GPR M F", integer=True)
# F0 es variable simbólica (valor desconocido al inicio)


def _not12(expr):
    """
    Complemento a 1 de 12 bits: ~x en aritmética de 12 bits = -x - 1
    (equivalente a XOR con 0xFFF)
    """
    return -expr - 1


def inferir(ops: list) -> str:
    """
    Simula simbólicamente la secuencia de ops y devuelve la instrucción
    de alto nivel que implementan (ej: 'M <- 3M - ACC').
    """
    if not ops:
        return "Sin instrucciones"

    ops = [op for op in ops if op]

    # ── Descartar fase fetch/decodificación ──────────────────────────
    FETCH_OPS = {"PC_TO_MAR", "INC_PC", "INC_GPR", "GPR_OP_TO_OPR"}
    while ops and ops[0] in FETCH_OPS:
        ops = ops[1:]

    if not ops:
        return "Ciclo fetch / decodificación"

    # ── Detectar si F se usa sin haber sido inicializado en 0 ────────
    # Ignorar ops de setup (carga de memoria, fetch) al buscar el primer uso de F
    SETUP_OPS = {"PC_TO_MAR", "INC_PC", "INC_GPR", "GPR_OP_TO_OPR",
                 "GPR_AD_TO_MAR", "M_TO_GPR", "GPR_TO_ACC", "ACC_TO_GPR",
                 "ZERO_ACC", "INC_ACC"}
    f_inicial = Integer(0)
    for op in ops:
        if op in SETUP_OPS:
            continue
        if op in ("ROL_F_ACC", "ROR_F_ACC"):
            f_inicial = F0   # F desconocido antes del primer ROL/ROR
            break
        if op == "ZERO_F":
            f_inicial = Integer(0)  # F explícitamente puesto en 0
            break

    # ── Estado simbólico inicial ─────────────────────────────────────
    state = {
        "ACC": ACC0,
        "GPR": GPR0,
        "M":   M0,
        "F":   f_inicial,
    }

    # ── Ejecutar cada operación simbólicamente ───────────────────────
    for op in ops:

        acc = state["ACC"]
        gpr = state["GPR"]
        m   = state["M"]
        f   = state["F"]

        if op == "INC_ACC":
            state["ACC"] = simplify(acc + 1)

        elif op == "INC_GPR":
            state["GPR"] = simplify(gpr + 1)

        elif op == "NOT_ACC":
            state["ACC"] = simplify(_not12(acc))

        elif op == "NOT_F":
            state["F"] = simplify(_not12(f))

        elif op == "ROL_F_ACC":
            # ROL: desplaza izquierda 1 bit con F como bit extra
            # F,ACC << 1  →  nuevo_F = bit_mas_significativo(ACC)
            # Como trabajamos simbólicamente, ROL = ACC * 2 + F (módulo 2^12)
            # F entra como bit menos significativo
            new_acc = simplify(acc * 2 + f)
            # el nuevo F sería el bit 12 de acc (overflow), tratamos como 0
            state["ACC"] = new_acc
            state["F"]   = Integer(0)  # F se considera consumido

        elif op == "ROR_F_ACC":
            # ROR: desplaza derecha 1 bit, F entra como bit más significativo
            # Resultado: (ACC + F*4096) / 2  pero expresado como entero
            # Cuando F=0: ACC >> 1 = ACC/2
            # Usamos división entera simbólica: floor(ACC/2) + F*2048
            from sympy import floor as sym_floor
            if f == Integer(0):
                new_acc = simplify(acc / 2)
            else:
                new_acc = simplify(acc / 2 + f * 2048)
            state["ACC"] = new_acc
            state["F"]   = Integer(0)

        elif op == "SUM_ACC_GPR":
            state["ACC"] = simplify(acc + gpr)

        elif op == "ACC_TO_GPR":
            state["GPR"] = state["ACC"]

        elif op == "GPR_TO_ACC":
            state["ACC"] = state["GPR"]

        elif op == "ZERO_ACC":
            state["ACC"] = Integer(0)

        elif op == "ZERO_F":
            state["F"] = Integer(0)

        elif op == "GPR_AD_TO_MAR":
            # Carga M desde RAM según dirección en GPR
            # Simbólicamente: M = M[GPR], lo representamos como M0
            state["M"] = M0

        elif op == "M_TO_GPR":
            state["GPR"] = state["M"]

        elif op == "GPR_TO_M":
            state["M"] = state["GPR"]

        elif op == "PC_TO_MAR":
            pass  # fetch, ignorado

        elif op == "INC_PC":
            pass  # ignorado

        elif op == "GPR_OP_TO_OPR":
            pass  # ignorado

        # ops no conocidas se ignoran silenciosamente

    # ── Determinar qué registros cambiaron ───────────────────────────
    iniciales = {"ACC": ACC0, "GPR": GPR0, "M": M0, "F": F0}
    cambios = {}
    for reg, inicial in iniciales.items():
        final = simplify(state[reg])
        if final != inicial:
            cambios[reg] = final

    if not cambios:
        return "Sin efecto observable"

    # ── Formatear expresión sympy a string legible ───────────────────
    def fmt(expr):
        from sympy import collect, Add
        import re
        # Intentar reordenar términos: positivos primero, negativos después
        try:
            args = Add.make_args(simplify(expr))
            pos = [a for a in args if not str(a).startswith('-')]
            neg = [a for a in args if str(a).startswith('-')]
            reordenado = simplify(sum(pos + neg, Integer(0)))
            s = str(reordenado)
        except Exception:
            s = str(simplify(expr))
        s = re.sub(r'(\d)\*([A-Z]+)', r'\1\2', s)    # 3*M -> 3M
        s = re.sub(r'(?<!\d)-1([A-Z])', r'-\1', s)   # -1ACC -> -ACC
        s = re.sub(r'([A-Z]+)/2', r'\1/2', s)         # ACC/2 se mantiene legible
        return s

    # ── Elegir el destino más relevante ─────────────────────────────
    # Si M cambió y su valor NO depende solo de GPR/ACC sin cambio real → mostrar M
    # Prioridad: M > ACC > GPR
    # Pero si M solo cambió por un GPR_TO_M al final, el resultado real es ACC
    lineas = []
    ultimo_op = ops[-1] if ops else ""

    if "M" in cambios and ultimo_op in ("GPR_TO_M", "M_TO_GPR"):
        lineas.append(f"M <- {fmt(cambios['M'])}")
    elif "ACC" in cambios:
        lineas.append(f"ACC <- {fmt(cambios['ACC'])}")
        if "M" in cambios and ultimo_op == "GPR_TO_M":
            lineas.append(f"M <- {fmt(cambios['M'])}")
    elif "M" in cambios:
        lineas.append(f"M <- {fmt(cambios['M'])}")

    if not lineas:
        lineas = [f"{r} <- {fmt(v)}" for r, v in cambios.items()]

    return "  |  ".join(lineas)
