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


def convertir(numero, base_origen, base_destino, precision=12):
    """Convierte un numero entre bases 2-36.

    Admite parte fraccionaria con punto y signo opcional.
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

    parte_entera = int(decimal_abs)
    parte_fraccion = decimal_abs - parte_entera

    entero_str = _entero_a_base(parte_entera, base_destino)
    fraccion_str = _fraccion_a_base(parte_fraccion, base_destino, precision)

    if fraccion_str:
        return f"{signo}{entero_str}.{fraccion_str}"
    return f"{signo}{entero_str}"
