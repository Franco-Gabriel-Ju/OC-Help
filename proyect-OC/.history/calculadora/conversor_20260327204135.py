from fractions import Fraction

_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class ConversionError(ValueError):
    """Error lanzado cuando una conversion de base no es valida."""


def _validar_base(base):
    if not isinstance(base, int):
        raise ConversionError("La base debe ser un entero.")
    if base < 2 or base > 36:
        raise ConversionError("La base debe estar entre 2 y 36.")


def _char_to_value(char):
    idx = _DIGITS.find(char)
    if idx == -1:
        raise ConversionError(f"Caracter invalido: '{char}'.")
    return idx


def _normalizar_numero(numero):
    if numero is None:
        raise ConversionError("El numero no puede ser None.")

    texto = str(numero).strip().upper().replace("_", "")
    texto = texto.replace(",", ".")
    if not texto:
        raise ConversionError("El numero no puede estar vacio.")

    signo = -1 if texto.startswith("-") else 1
    if texto[0] in "+-":
        texto = texto[1:]

    if not texto:
        raise ConversionError("No se encontro un valor numerico.")

    if texto.count(".") > 1:
        raise ConversionError("El numero tiene mas de un punto decimal.")

    if "." in texto:
        parte_entera, parte_fraccion = texto.split(".", 1)
    else:
        parte_entera, parte_fraccion = texto, ""

    if parte_entera == "":
        parte_entera = "0"

    return signo, parte_entera, parte_fraccion


def _a_decimal(numero, base_origen):
    _validar_base(base_origen)
    signo, parte_entera, parte_fraccion = _normalizar_numero(numero)

    total = Fraction(0, 1)

    for char in parte_entera:
        valor = _char_to_value(char)
        if valor >= base_origen:
            raise ConversionError(
                f"Digito '{char}' invalido para base {base_origen}."
            )
        total = total * base_origen + valor

    factor = Fraction(1, base_origen)
    for char in parte_fraccion:
        valor = _char_to_value(char)
        if valor >= base_origen:
            raise ConversionError(
                f"Digito '{char}' invalido para base {base_origen}."
            )
        total += valor * factor
        factor /= base_origen

    return total if signo > 0 else -total


def _entero_a_base(valor_entero, base_destino):
    if valor_entero == 0:
        return "0"

    digitos = []
    n = valor_entero
    while n > 0:
        n, rem = divmod(n, base_destino)
        digitos.append(_DIGITS[rem])
    return "".join(reversed(digitos))


def _fraccion_a_base(fraccion, base_destino, precision):
    if fraccion == 0:
        return ""

    digitos = []
    actual = fraccion
    for _ in range(precision):
        actual *= base_destino
        entero = int(actual)
        digitos.append(_DIGITS[entero])
        actual -= entero
        if actual == 0:
            break

    return "".join(digitos)


def _redondear_absoluto_en_base(decimal_abs, base_destino, precision):
    """Redondea el valor absoluto en la base destino a `precision` cifras fraccionarias."""
    escala = base_destino ** precision
    escalado = decimal_abs * escala

    q, r = divmod(escalado.numerator, escalado.denominator)
    # Redondeo half-up sobre el valor absoluto.
    if r * 2 >= escalado.denominator:
        q += 1

    parte_entera, parte_fraccion = divmod(q, escala)
    entero_str = _entero_a_base(parte_entera, base_destino)

    if precision == 0:
        return entero_str, ""

    fraccion_digitos = []
    for i in range(precision - 1, -1, -1):
        base_pow = base_destino ** i
        digito, parte_fraccion = divmod(parte_fraccion, base_pow)
        fraccion_digitos.append(_DIGITS[digito])

    return entero_str, "".join(fraccion_digitos)


def _complemento_base_hibrido(entero_abs, fraccion_abs, base_destino, complemento):
    """Aplica metodo de mascara hibrida: C_{n-1} o C_n en la base destino."""
    precision = len(fraccion_abs)
    cantidad_valor = len(entero_abs) + precision
    total_digitos = 1 + cantidad_valor

    if cantidad_valor <= 0:
        raise ConversionError("No hay digitos de valor para aplicar complemento.")

    valor_maximo = base_destino - 1
    escala = base_destino ** precision

    valor_abs = _a_decimal(f"{entero_abs}.{fraccion_abs}" if precision else entero_abs, base_destino)
    sustraendo = int(valor_abs * escala)

    # Mascara: 1 seguido de (base-1) en todos los digitos de valor.
    mascara = (base_destino ** cantidad_valor) + (base_destino ** cantidad_valor - 1)

    # Paso 3: C_{n-1} = mascara - sustraendo
    complemento_bn1 = mascara - sustraendo
    resultado_escalado = complemento_bn1

    # Paso 4: C_n = C_{n-1} + 1 ULP
    if complemento in ("complemento", "a_dos", "base"):
        resultado_escalado += 1

    if resultado_escalado < 0:
        raise ConversionError("No se pudo calcular el complemento en la base destino.")

    # Formateo fijo: 1 digito de signo + digitos de valor.
    resultado_base = _entero_a_base(resultado_escalado, base_destino).zfill(total_digitos)
    if len(resultado_base) > total_digitos:
        raise ConversionError("El resultado excede la longitud esperada del complemento.")

    if precision == 0:
        return resultado_base

    entero = resultado_base[:-precision]
    fraccion = resultado_base[-precision:]
    return f"{entero}.{fraccion}"


def descomplementar(numero_complementado, base_origen, separador="."):
    """Convierte un valor en notacion complementada a notacion con signo explicito.

    Regla usada:
    - Si el digito de signo es 0, el numero es positivo y el valor queda igual.
    - Si el digito de signo es 1, se deshace C_n:
      1) restar 1 ULP
      2) mascara - resultado para recuperar el valor absoluto
      3) aplicar signo negativo
    """
    _validar_base(base_origen)

    texto = str(numero_complementado).strip().upper().replace(separador, ".").replace(",", ".")
    if not texto:
        raise ConversionError("El numero complementado no puede estar vacio.")

    if texto[0] in "+-":
        texto = texto[1:]

    if texto.count(".") > 1:
        raise ConversionError("El numero tiene mas de un separador fraccionario.")

    if "." in texto:
        parte_entera, parte_fraccion = texto.split(".", 1)
    else:
        parte_entera, parte_fraccion = texto, ""

    if not parte_entera:
        raise ConversionError("Falta la parte entera del numero complementado.")

    for ch in parte_entera + parte_fraccion:
        if _char_to_value(ch) >= base_origen:
            raise ConversionError(f"Digito '{ch}' invalido para base {base_origen}.")

    signo_digit = _char_to_value(parte_entera[0])
    if signo_digit not in (0, 1):
        raise ConversionError("En notacion complementada, el primer digito debe ser 0 o 1.")

    valor_entera = parte_entera[1:] if len(parte_entera) > 1 else "0"
    precision = len(parte_fraccion)

    if signo_digit == 0:
        resultado = f"+{valor_entera}"
        if precision:
            resultado += f".{parte_fraccion}"
        return resultado.replace(".", separador)

    # Caso negativo: deshacer complemento a la base C_n
    cantidad_valor = len(valor_entera) + precision
    if cantidad_valor <= 0:
        raise ConversionError("Formato complementado invalido.")

    escala = base_origen ** precision
    valor_comp = _a_decimal(texto, base_origen)
    valor_comp_escalado = int(valor_comp * escala)

    # C_{n-1} = C_n - 1 ULP
    valor_c_n_1 = valor_comp_escalado - 1

    # mascara = 1 seguido de (base-1) para todos los digitos de valor
    mascara = (base_origen ** cantidad_valor) + (base_origen ** cantidad_valor - 1)

    abs_escalado = mascara - valor_c_n_1
    if abs_escalado < 0:
        raise ConversionError("No se pudo descomplementar el valor.")

    abs_entero, abs_frac = divmod(abs_escalado, escala)
    abs_entero_str = _entero_a_base(abs_entero, base_origen).zfill(len(valor_entera))

    if precision:
        frac_digits = []
        rest = abs_frac
        for i in range(precision - 1, -1, -1):
            pow_base = base_origen ** i
            dig, rest = divmod(rest, pow_base)
            frac_digits.append(_DIGITS[dig])
        abs_frac_str = "".join(frac_digits)
        return f"-{abs_entero_str}.{abs_frac_str}".replace(".", separador)

    return f"-{abs_entero_str}"


def _aplicar_complemento_a_uno(binario_str, bits_totales):
    """Aplica complemento a uno: invierte cada bit."""
    binario_str = binario_str.replace(".", "")
    if len(binario_str) > bits_totales:
        raise ConversionError(f"El numero requiere mas de {bits_totales} bits.")

    binario_str = binario_str.zfill(bits_totales)
    complemento = "".join("1" if b == "0" else "0" for b in binario_str)
    return complemento


def _aplicar_complemento_a_dos(binario_str, bits_totales):
    """Aplica complemento a dos: complemento a uno + 1."""
    comp_uno = _aplicar_complemento_a_uno(binario_str, bits_totales)

    decimal_comp_uno = _a_decimal(comp_uno, 2)
    decimal_comp_dos = decimal_comp_uno + 1

    return _entero_a_base(int(decimal_comp_dos), 2).zfill(bits_totales)


def convertir(numero, base_origen, base_destino, precision=12, complemento=None, bits_complemento=None, separador="."):
    """Convierte un numero entre bases 2-36.

    Admite parte fraccionaria con punto o coma y signo opcional.
    Si `complemento` esta activo, aplica complemento a la base (C_n)
    usando mascara hibrida en la base destino. En binario equivale a C2.
    """
    _validar_base(base_origen)
    _validar_base(base_destino)

    if not isinstance(precision, int) or precision < 0:
        raise ConversionError("La precision debe ser un entero >= 0.")

    decimal = _a_decimal(numero, base_origen)
    if decimal == 0:
        return "0"

    signo = "-" if decimal < 0 else ""
    decimal_abs = abs(decimal)

    entero_str, fraccion_str = _redondear_absoluto_en_base(decimal_abs, base_destino, precision)

    # En negativos, el complemento se hace en la base destino con mascara hibrida.
    if complemento and signo == "-":
        if complemento not in ("complemento", "a_dos", "base"):
            raise ConversionError("Complemento invalido. Use 'complemento'.")

        resultado = _complemento_base_hibrido(
            entero_str,
            fraccion_str,
            base_destino,
            complemento,
        )
        return resultado.replace(".", separador)

    resultado = f"{signo}{entero_str}"
    if fraccion_str:
        resultado += f"{separador}{fraccion_str}"
    else:
        resultado = f"{signo}{entero_str}"

    return resultado
