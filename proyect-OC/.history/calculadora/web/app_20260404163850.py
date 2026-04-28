from pathlib import Path
import math
import sys

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from conversor import (  # noqa: E402
    ConversionError,
    _a_decimal,
    _entero_a_base,
    _normalizar_numero,
    _redondear_absoluto_en_base,
    convertir,
    convertir_nc_a_nc,
    descomplementar,
    operar_nc_didactico,
)


app = Flask(__name__, template_folder="templates", static_folder="static")


def _to_int(value, name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ConversionError(f"{name} debe ser un entero.")


def _explicito_a_cs_signo_bit(explicito, enteros_totales, fracc_fijas, separador):
    if not isinstance(enteros_totales, int) or enteros_totales < 1:
        raise ConversionError("E debe ser un entero >= 1.")
    if not isinstance(fracc_fijas, int) or fracc_fijas < 0:
        raise ConversionError("F debe ser un entero >= 0.")

    texto = str(explicito).strip().upper().replace(separador, ".").replace(",", ".")
    if not texto:
        raise ConversionError("El valor explicito no puede estar vacio.")

    signo_bit = "1" if texto.startswith("-") else "0"
    if texto[0] in "+-":
        texto = texto[1:]

    if "." in texto:
        parte_entera, parte_frac = texto.split(".", 1)
    else:
        parte_entera, parte_frac = texto, ""

    valor_enteros = enteros_totales - 1
    parte_entera = parte_entera.zfill(valor_enteros) if valor_enteros > 0 else ""
    parte_frac = parte_frac.ljust(fracc_fijas, "0")[:fracc_fijas]

    salida = signo_bit + parte_entera
    if fracc_fijas > 0:
        salida += f"{separador}{parte_frac}"
    return salida


def _fmt_fraction(value):
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator} (~{float(value):.10f})"


def _pasos_expansion_posicional(numero, base_origen):
    signo, parte_entera, parte_fraccion = _normalizar_numero(numero)
    digitos = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    detalle = []
    detalle.append("Expansion posicional (base origen):")

    terminos_enteros = []
    potencia = len(parte_entera) - 1
    for ch in parte_entera:
        valor = digitos.index(ch)
        terminos_enteros.append(f"{valor}*{base_origen}^{potencia}")
        potencia -= 1

    terminos_frac = []
    for idx, ch in enumerate(parte_fraccion, start=1):
        valor = digitos.index(ch)
        terminos_frac.append(f"{valor}*{base_origen}^-{idx}")

    if terminos_enteros:
        detalle.append("  Parte entera = " + " + ".join(terminos_enteros))
    if terminos_frac:
        detalle.append("  Parte fraccion = " + " + ".join(terminos_frac))

    decimal = _a_decimal(numero, base_origen)
    detalle.append(f"  Valor decimal exacto = {_fmt_fraction(decimal)}")
    if signo < 0:
        detalle.append("  Signo detectado: -")

    return detalle


def _pasos_descomplementar(numero, base_origen, enteros_totales, fracc_fijas, separador):
    digitos = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    texto = str(numero).strip().upper().replace(separador, ".").replace(",", ".")
    if texto and texto[0] in "+-":
        texto = texto[1:]

    if "." in texto:
        parte_entera, parte_fraccion = texto.split(".", 1)
    else:
        parte_entera, parte_fraccion = texto, ""

    if enteros_totales is not None:
        parte_entera = parte_entera.zfill(enteros_totales)

    precision = len(parte_fraccion)
    if fracc_fijas is not None:
        if precision < fracc_fijas:
            parte_fraccion = parte_fraccion.ljust(fracc_fijas, "0")
        elif precision > fracc_fijas:
            parte_fraccion = parte_fraccion[:fracc_fijas]
        precision = fracc_fijas

    texto_ajustado = parte_entera + ("." + parte_fraccion if precision else "")
    signo_digit = digitos.index(parte_entera[0])
    valor_entera = parte_entera[1:] if len(parte_entera) > 1 else "0"

    detalle = []
    detalle.append("Descomplementacion (entrada ya complementada):")
    detalle.append(f"  Texto ajustado: {texto_ajustado.replace('.', separador)}")
    detalle.append(f"  Digito de signo = {parte_entera[0]} -> {signo_digit}")

    if signo_digit == 0:
        explicito = f"+{valor_entera}"
        if precision:
            explicito += f"{separador}{parte_fraccion}"
        detalle.append("  Como signo=0, el valor ya es positivo.")
        detalle.append(f"  Resultado explicito: {explicito}")
        return explicito, detalle

    cantidad_valor = len(valor_entera) + precision
    escala = base_origen ** precision
    valor_comp = _a_decimal(texto_ajustado, base_origen)
    valor_comp_escalado = int(valor_comp * escala)
    valor_c_n_1 = valor_comp_escalado - 1
    mascara = (base_origen ** cantidad_valor) + (base_origen ** cantidad_valor - 1)
    abs_escalado = mascara - valor_c_n_1
    abs_entero, abs_frac = divmod(abs_escalado, escala)
    abs_entero_str = _entero_a_base(abs_entero, base_origen).zfill(len(valor_entera))

    detalle.append("  Como signo=1, se usa inversa de Cn:")
    detalle.append(f"  escala = B^F = {base_origen}^{precision} = {escala}")
    detalle.append(f"  valor_comp = {_fmt_fraction(valor_comp)}")
    detalle.append(f"  valor_comp_escalado = valor_comp * escala = {valor_comp_escalado}")
    detalle.append(f"  C_(n-1) = C_n - 1 = {valor_c_n_1}")
    detalle.append(
        f"  mascara = B^n + (B^n-1) = {base_origen}^{cantidad_valor} + ({base_origen}^{cantidad_valor}-1) = {mascara}"
    )
    detalle.append(f"  abs_escalado = mascara - C_(n-1) = {abs_escalado}")

    if precision:
        frac_digits = []
        rest = abs_frac
        for i in range(precision - 1, -1, -1):
            pow_base = base_origen ** i
            dig, rest = divmod(rest, pow_base)
            frac_digits.append(digitos[dig])
        abs_frac_str = "".join(frac_digits)
        explicito = f"-{abs_entero_str}{separador}{abs_frac_str}"
    else:
        explicito = f"-{abs_entero_str}"

    detalle.append(f"  Resultado explicito: {explicito}")
    return explicito, detalle


def _precision_minima_exacta(numero_entrada, base_origen, base_destino):
    bits_por_digito = {2: 1, 8: 3, 16: 4}
    if base_origen not in bits_por_digito or base_destino not in bits_por_digito:
        return 0

    texto = numero_entrada.strip().upper().replace(",", ".")
    if texto.startswith("+") or texto.startswith("-"):
        texto = texto[1:]
    if "." not in texto:
        return 0

    frac_len_origen = len(texto.split(".", 1)[1])
    if frac_len_origen <= 0:
        return 0

    return math.ceil(frac_len_origen * bits_por_digito[base_origen] / bits_por_digito[base_destino])


def _ajustar_salida_fraccion_binaria(salida, numero_entrada, base_origen, base_destino, separador):
    bits_por_digito = {2: 1, 8: 3, 16: 4}
    if base_origen not in bits_por_digito or base_destino not in bits_por_digito:
        return salida

    texto = numero_entrada.strip().upper().replace(",", ".")
    if texto.startswith("+") or texto.startswith("-"):
        texto = texto[1:]

    if "." not in texto:
        return salida

    frac_len_origen = len(texto.split(".", 1)[1])
    if frac_len_origen == 0:
        return salida

    min_digitos = math.ceil(frac_len_origen * bits_por_digito[base_origen] / bits_por_digito[base_destino])
    if min_digitos <= 0 or separador not in salida:
        return salida

    parte_entera, parte_frac = salida.split(separador, 1)
    if len(parte_frac) <= min_digitos:
        return salida

    sobrante = parte_frac[min_digitos:]
    if any(ch != "0" for ch in sobrante):
        return salida

    return f"{parte_entera}{separador}{parte_frac[:min_digitos]}"


def _quitar_fraccion_si_entero(salida, numero_entrada, base_origen, separador):
    valor_decimal = _a_decimal(numero_entrada, base_origen)
    if valor_decimal.denominator != 1 or separador not in salida:
        return salida

    parte_entera, parte_frac = salida.split(separador, 1)
    if not parte_frac:
        return parte_entera

    if any(ch != "0" for ch in parte_frac):
        return salida

    return parte_entera


def _abreviacion_nc(numero_entrada, base_origen, separador):
    texto = numero_entrada.strip().upper().replace(",", ".")
    if texto.startswith("+") or texto.startswith("-"):
        texto = texto[1:]

    if "." in texto:
        parte_entera, parte_fraccion = texto.split(".", 1)
    else:
        parte_entera, parte_fraccion = texto, ""

    if not parte_entera:
        parte_entera = "0"

    if base_origen == 2:
        bits_por_digito = 1
    elif base_origen == 8:
        bits_por_digito = 3
    elif base_origen == 16:
        bits_por_digito = 4
    else:
        bits_por_digito = math.ceil(math.log2(base_origen))

    bits_aprox = len(parte_entera) * bits_por_digito
    ancho_bits = max(1, math.ceil(bits_aprox / 8) * 8)

    numero_formateado = parte_entera
    if parte_fraccion:
        numero_formateado += f"{separador}{parte_fraccion}"

    return f"{numero_formateado} ({ancho_bits},{len(parte_entera)},{len(parte_fraccion)})NC"


def _tokenizar_expresion(expresion):
    expr = str(expresion).strip().upper().replace("X", "*").replace("÷", "/")
    tokens = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue

        if ch.isalnum() or ch in ".,":
            j = i
            while j < len(expr) and (expr[j].isalnum() or expr[j] in ".,"):
                j += 1
            tokens.append(expr[i:j])
            i = j
            continue

        if ch in "+-*/()":
            tokens.append(ch)
            i += 1
            continue

        raise ConversionError(f"Caracter invalido en expresion: '{ch}'.")

    if not tokens:
        raise ConversionError("La expresion esta vacia.")
    return tokens


def _evaluar_expresion_base(expresion, base_origen):
    tokens = _tokenizar_expresion(expresion)
    idx = 0

    def current():
        return tokens[idx] if idx < len(tokens) else None

    def parse_factor():
        nonlocal idx
        tok = current()
        if tok is None:
            raise ConversionError("Expresion incompleta.")

        if tok == "+":
            idx += 1
            return parse_factor()
        if tok == "-":
            idx += 1
            return -parse_factor()
        if tok == "(":
            idx += 1
            val = parse_expr()
            if current() != ")":
                raise ConversionError("Falta ')' en la expresion.")
            idx += 1
            return val

        idx += 1
        return _a_decimal(tok, base_origen)

    def parse_term():
        nonlocal idx
        val = parse_factor()
        while current() in ("*", "/"):
            op = current()
            idx += 1
            right = parse_factor()
            if op == "*":
                val *= right
            else:
                if right == 0:
                    raise ConversionError("Division por cero en la expresion.")
                val /= right
        return val

    def parse_expr():
        nonlocal idx
        val = parse_term()
        while current() in ("+", "-"):
            op = current()
            idx += 1
            right = parse_term()
            if op == "+":
                val += right
            else:
                val -= right
        return val

    result = parse_expr()
    if idx != len(tokens):
        raise ConversionError("Expresion invalida: sobran tokens sin procesar.")
    return result


def _fraction_a_texto_base(valor_decimal, base_origen, precision, separador):
    signo = "-" if valor_decimal < 0 else ""
    abs_val = -valor_decimal if valor_decimal < 0 else valor_decimal
    entero, frac = _redondear_absoluto_en_base(abs_val, base_origen, precision)
    if precision <= 0:
        return f"{signo}{entero}"

    frac = frac.rstrip("0")
    if not frac:
        return f"{signo}{entero}"
    return f"{signo}{entero}{separador}{frac}"


def _group_from_right(texto, size):
    if not texto:
        return []
    mod = len(texto) % size
    padded = ("0" * (size - mod) + texto) if mod else texto
    return [padded[i:i + size] for i in range(0, len(padded), size)]


def _group_from_left(texto, size):
    if not texto:
        return []
    mod = len(texto) % size
    padded = (texto + "0" * (size - mod)) if mod else texto
    return [padded[i:i + size] for i in range(0, len(padded), size)]


def _manual_conversion_target(
    numero,
    base_origen,
    base_dest,
    separador,
    precision_obj,
    complemento,
    enteros_valor_fijos,
    resultado,
):
    detalle = []
    detalle.append(f"RESOLUCION MANUAL: base {base_origen} -> base {base_dest}")
    detalle.append(f"Entrada: {numero}")
    detalle.append("")

    detalle.append("1) Expansion posicional en base origen:")
    for ln in _pasos_expansion_posicional(numero, base_origen):
        detalle.append("   " + ln)

    valor_decimal = _a_decimal(numero, base_origen)
    abs_decimal = -valor_decimal if valor_decimal < 0 else valor_decimal

    detalle.append("")
    detalle.append("2) Metodo de conversion:")
    if base_origen in (2, 8, 16) and base_dest in (2, 8, 16):
        bits_map = {2: 1, 8: 3, 16: 4}
        bits_o = bits_map[base_origen]
        bits_d = bits_map[base_dest]
        signo, parte_entera, parte_frac = _normalizar_numero(numero)
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        ent_bits = "".join(format(digits.index(ch), f"0{bits_o}b") for ch in parte_entera)
        frac_bits = "".join(format(digits.index(ch), f"0{bits_o}b") for ch in parte_frac)
        ent_groups = _group_from_right(ent_bits, bits_d)
        frac_groups = _group_from_left(frac_bits, bits_d)

        detalle.append("   Se usa puente binario (agrupacion de bits).")
        detalle.append(f"   Cada digito en base {base_origen} equivale a {bits_o} bit(s).")
        detalle.append(f"   Parte entera en bits: {ent_bits or '0'}")
        if parte_frac:
            detalle.append(f"   Parte fraccionaria en bits: {frac_bits}")
        detalle.append(f"   Reagrupamos en bloques de {bits_d} bit(s) para base {base_dest}:")
        detalle.append(f"   Entera: {' | '.join(ent_groups) if ent_groups else '0'}")
        if frac_groups:
            detalle.append(f"   Fraccion: {' | '.join(frac_groups)}")
        if signo < 0:
            detalle.append("   El signo negativo se conserva para la conversion explicita.")
    else:
        detalle.append("   Se usa metodo general: decimal intermedio + divisiones/multiplicaciones sucesivas.")
        detalle.append(f"   Valor decimal exacto: {_fmt_fraction(valor_decimal)}")

        ent = int(abs_decimal)
        frac = abs_decimal - ent
        detalle.append("")
        detalle.append("   2.a) Parte entera por divisiones sucesivas:")
        if ent == 0:
            detalle.append(f"      0 / {base_dest} = 0  (resto 0)")
        else:
            current = ent
            restos = []
            while current > 0:
                q, r = divmod(current, base_dest)
                restos.append(r)
                detalle.append(f"      {current:>10} / {base_dest} = {q:>10}   resto {r}")
                current = q
            restos_text = " ".join(str(r) for r in reversed(restos))
            detalle.append("      " + "-" * 42)
            detalle.append(f"      Lectura de restos (de abajo hacia arriba): {restos_text}")

        if precision_obj > 0:
            detalle.append("")
            detalle.append("   2.b) Parte fraccionaria por multiplicaciones sucesivas:")
            cur = frac
            for i in range(1, precision_obj + 1):
                prod = cur * base_dest
                dig = int(prod)
                nxt = prod - dig
                detalle.append(
                    f"      Paso {i}: ({_fmt_fraction(cur)})*{base_dest} = {_fmt_fraction(prod)} -> digito {dig}, resto {_fmt_fraction(nxt)}"
                )
                cur = nxt
                if cur == 0:
                    break

    detalle.append("")
    detalle.append("3) Resultado en base destino:")
    detalle.append(f"   {resultado}")

    if complemento and str(numero).startswith("-"):
        detalle.append("")
        detalle.append("4) Codificacion por complemento (visual tipo primaria):")
        signo, ent_s, frac_s = _normalizar_numero(resultado)
        if signo < 0:
            abs_res = resultado[1:] if resultado.startswith("-") else resultado
            if separador in abs_res:
                epart, fpart = abs_res.split(separador, 1)
            elif "." in abs_res:
                epart, fpart = abs_res.split(".", 1)
            else:
                epart, fpart = abs_res, ""

            if enteros_valor_fijos is not None:
                epart = epart.zfill(enteros_valor_fijos)

            precision_comp = len(fpart)
            cantidad_valor = len(epart) + precision_comp
            escala_comp = base_dest ** precision_comp
            valor_abs_comp = _a_decimal(f"{epart}.{fpart}" if precision_comp else epart, base_dest)
            sustraendo = int(valor_abs_comp * escala_comp)
            mascara = (base_dest ** cantidad_valor) + (base_dest ** cantidad_valor - 1)
            c_n_1 = mascara - sustraendo
            c_n = c_n_1 + 1
            detalle.append(f"   Mascara = {mascara}")
            detalle.append(f"   {mascara}")
            detalle.append(f" - {sustraendo}")
            detalle.append(f"   {'-' * max(len(str(mascara)), len(str(sustraendo)))}")
            detalle.append(f"   {c_n_1}   (C_(n-1))")
            detalle.append(f" + 1")
            detalle.append(f"   {'-' * max(len(str(c_n_1)), 1)}")
            detalle.append(f"   {c_n}   (C_n)")

    return "\n".join(detalle)


def _manual_conversion_target_data(
    numero,
    base_origen,
    base_dest,
    separador,
    resultado,
    *,
    entrada_original,
    entrada_ya_comp,
    redondear,
    precision_ui,
    precision_obj,
    min_precision_exacta,
    nc_fijo,
    fracc_fijas,
    complemento,
):
    data = {
        "titulo": f"base {base_origen} -> base {base_dest}",
        "entrada": numero,
        "pasos": [],
    }

    signo, parte_entera, parte_frac = _normalizar_numero(numero)
    digitos = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    terminos_ent = []
    potencia = len(parte_entera) - 1
    for ch in parte_entera:
        terminos_ent.append(f"{digitos.index(ch)}\\cdot {base_origen}^{{{potencia}}}")
        potencia -= 1

    terminos_frac = []
    for i, ch in enumerate(parte_frac, start=1):
        terminos_frac.append(f"{digitos.index(ch)}\\cdot {base_origen}^{{-{i}}}")

    valor_decimal = _a_decimal(numero, base_origen)
    eq_exp = " + ".join(terminos_ent + terminos_frac) if (terminos_ent or terminos_frac) else "0"
    data["pasos"].append(
        {
            "titulo": "0) Configuración aplicada",
            "nota": "Estas opciones afectan cómo se interpreta y se convierte el número.",
            "lineas": [
                f"Entrada original: {entrada_original}",
                f"Valor ya complementado: {'SI' if entrada_ya_comp else 'NO'}",
                f"Redondear: {'SI' if redondear else 'NO'}",
                f"NC fijo: {'SI' if nc_fijo else 'NO'}",
                f"Aplicar complemento: {'SI' if complemento else 'NO'}",
            ],
        }
    )

    if entrada_ya_comp:
        _, trazas = _pasos_descomplementar(entrada_original, base_origen, None, None, separador)
        data["pasos"].append(
            {
                "titulo": "0.1) Descomplementación",
                "nota": "Como el valor estaba marcado como complementado, primero se obtiene el valor explícito.",
                "lineas": trazas,
            }
        )

    data["pasos"].append(
        {
            "titulo": "1) Expansión posicional",
            "nota": "Se reemplaza cada dígito por su valor multiplicado por la potencia de la base.",
            "ecuaciones": [
                f"V = {eq_exp}",
                f"V_{{10}} = {_fmt_fraction(valor_decimal)}",
            ],
        }
    )

    if base_origen in (2, 8, 16) and base_dest in (2, 8, 16):
        bits_map = {2: 1, 8: 3, 16: 4}
        bits_o = bits_map[base_origen]
        bits_d = bits_map[base_dest]
        ent_bits = "".join(format(digitos.index(ch), f"0{bits_o}b") for ch in parte_entera)
        frac_bits = "".join(format(digitos.index(ch), f"0{bits_o}b") for ch in parte_frac)
        ent_groups = _group_from_right(ent_bits, bits_d)
        frac_groups = _group_from_left(frac_bits, bits_d)
        data["pasos"].append(
            {
                "titulo": "3) Puente binario",
                "nota": "Como ambas bases son potencias de 2, se convierte por agrupación de bits.",
                "ecuaciones": [
                    f"1\\text{{ dígito en base }}{base_origen} = {bits_o}\\text{{ bit(s)}}",
                    f"\\text{{Agrupar en bloques de }}{bits_d}\\text{{ bit(s) para base }}{base_dest}",
                ],
                "bits": {
                    "entera": ent_groups,
                    "fraccion": frac_groups,
                    "ent_bits": ent_bits or "0",
                    "frac_bits": frac_bits,
                },
            }
        )
    else:
        data["pasos"].append(
            {
                "titulo": "3) Método general",
                "nota": "Se usa decimal intermedio, divisiones sucesivas (entera) y multiplicaciones sucesivas (fracción).",
                "ecuaciones": [f"V_{{10}} = {_fmt_fraction(valor_decimal)}"],
            }
        )

    data["pasos"].append(
        {
            "titulo": "2) Redondeo y precisión",
            "nota": "Se define cuántas cifras fraccionarias se conservan en la base destino.",
            "lineas": [
                f"precision_ui = {precision_ui}",
                f"precision_minima_exacta = {min_precision_exacta}",
                f"precision_objetivo = {precision_obj}",
                (
                    f"fracc_fijas (NC fijo) = {fracc_fijas}"
                    if fracc_fijas is not None
                    else "fracc_fijas (NC fijo) = no aplica"
                ),
            ],
        }
    )

    data["pasos"].append(
        {
            "titulo": "4) Resultado",
            "nota": "Se obtiene el número final en la base destino.",
            "ecuaciones": [f"V_{{{base_dest}}} = {resultado.replace(',', '{,}')}"] if separador == "," else [f"V_{{{base_dest}}} = {resultado}"],
        }
    )

    if signo < 0:
        data["pasos"].append(
            {
                "titulo": "5) Signo",
                "nota": "El signo negativo se conserva durante la conversión explícita.",
                "ecuaciones": ["\\text{Signo} = -"],
            }
        )

    if complemento and str(numero).startswith("-"):
        data["pasos"].append(
            {
                "titulo": "6) Complementación en destino",
                "nota": "Como aplicar complemento está activo y el valor es negativo, se codifica en C_n en la base destino.",
                "lineas": [
                    "Se usa máscara híbrida: C_(n-1) = mascara - valor_abs_escalado, luego C_n = C_(n-1) + 1.",
                    "Este mismo cálculo es el que produce la salida complementada final.",
                ],
            }
        )

    return data


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/convert")
def api_convert():
    data = request.get_json(force=True)
    try:
        numero = str(data.get("numero", "")).strip()
        base_origen = _to_int(data.get("base_origen"), "base_origen")
        base_destino = _to_int(data.get("base_destino"), "base_destino")
        precision = _to_int(data.get("precision", 12), "precision")
        separador = data.get("separador", ",")
        complemento = "complemento" if bool(data.get("complemento", False)) else None

        enteros_valor_fijos = data.get("enteros_valor_fijos")
        if enteros_valor_fijos is not None and enteros_valor_fijos != "":
            enteros_valor_fijos = _to_int(enteros_valor_fijos, "enteros_valor_fijos")
        else:
            enteros_valor_fijos = None

        resultado = convertir(
            numero,
            base_origen,
            base_destino,
            precision=precision,
            complemento=complemento,
            separador=separador,
            enteros_valor_fijos=enteros_valor_fijos,
        )
        resultado = _quitar_fraccion_si_entero(resultado, numero, base_origen, separador)
        return jsonify({"ok": True, "resultado": resultado})
    except ConversionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/eval-expression")
def api_eval_expression():
    data = request.get_json(force=True)
    try:
        expresion = str(data.get("expresion", "")).strip()
        base_origen = _to_int(data.get("base_origen"), "base_origen")
        precision = _to_int(data.get("precision", 8), "precision")
        separador = data.get("separador", ",")

        valor = _evaluar_expresion_base(expresion, base_origen)
        resultado = _fraction_a_texto_base(valor, base_origen, precision, separador)
        return jsonify({"ok": True, "resultado": resultado, "decimal": _fmt_fraction(valor)})
    except ConversionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/convert-all")
def api_convert_all():
    data = request.get_json(force=True)
    try:
        numero = str(data.get("numero", "")).strip().upper()
        if not numero or numero in ("-", "+"):
            raise ConversionError("Escribe un numero valido.")

        base_origen = _to_int(data.get("base_origen"), "base_origen")
        precision = _to_int(data.get("precision", 4), "precision")
        separador = data.get("separador", ",")
        redondear = bool(data.get("redondear", True))
        entrada_ya_comp = bool(data.get("entrada_complementada", False))
        nc_fijo = bool(data.get("nc_fijo", False))
        complemento = "complemento" if bool(data.get("complemento", False)) else None

        enteros_fijos = _to_int(data.get("e"), "e") if nc_fijo else None
        fracc_fijas = _to_int(data.get("f"), "f") if nc_fijo else None
        nc_base_fija = _to_int(data.get("base_nc"), "base_nc") if nc_fijo else None

        if entrada_ya_comp:
            numero = descomplementar(
                numero,
                base_origen,
                separador=separador,
                enteros_totales=enteros_fijos,
                fracc_fijas=fracc_fijas,
            )
            complemento = None

        aviso = "Entrada complementada detectada. Se ajustaron las opciones necesarias." if entrada_ya_comp else None

        bases = {"DEC": 10, "BIN": 2, "HEX": 16, "OCT": 8}
        resultados = {}

        for key, base_dest in bases.items():
            min_precision_exacta = _precision_minima_exacta(numero, base_origen, base_dest)
            respetar_precision_objetivo = nc_fijo or entrada_ya_comp

            if redondear:
                precision_base = fracc_fijas if fracc_fijas is not None else precision
                precision_objetivo = precision_base if respetar_precision_objetivo else max(precision_base, min_precision_exacta)
            else:
                precision_objetivo = 16 if respetar_precision_objetivo else max(16, min_precision_exacta)

            salida = convertir(
                numero,
                base_origen,
                base_dest,
                precision=precision_objetivo,
                complemento=complemento,
                bits_complemento=None,
                separador=separador,
                enteros_valor_fijos=(enteros_fijos - 1)
                if enteros_fijos is not None and complemento and base_dest == nc_base_fija
                else None,
            )
            salida = _ajustar_salida_fraccion_binaria(salida, numero, base_origen, base_dest, separador)
            salida = _quitar_fraccion_si_entero(salida, numero, base_origen, separador)
            resultados[key] = salida

        return jsonify(
            {
                "ok": True,
                "entrada_normalizada": numero,
                "abreviacion": _abreviacion_nc(numero, base_origen, separador),
                "resultados": resultados,
                "aviso": aviso,
            }
        )
    except ConversionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/manual-target")
def api_manual_target():
    data = request.get_json(force=True)
    try:
        numero = str(data.get("numero", "")).strip().upper()
        entrada_original = numero
        if not numero or numero in ("-", "+"):
            raise ConversionError("Escribe un numero valido.")

        base_origen = _to_int(data.get("base_origen"), "base_origen")
        target = str(data.get("target", "DEC")).upper()
        bases = {"DEC": 10, "BIN": 2, "HEX": 16, "OCT": 8}
        if target not in bases:
            raise ConversionError("target invalido. Use DEC/BIN/HEX/OCT.")
        base_dest = bases[target]

        precision = _to_int(data.get("precision", 4), "precision")
        separador = data.get("separador", ",")
        redondear = bool(data.get("redondear", True))
        entrada_ya_comp = bool(data.get("entrada_complementada", False))
        nc_fijo = bool(data.get("nc_fijo", False))
        complemento = "complemento" if bool(data.get("complemento", False)) else None

        enteros_fijos = _to_int(data.get("e"), "e") if nc_fijo else None
        fracc_fijas = _to_int(data.get("f"), "f") if nc_fijo else None
        nc_base_fija = _to_int(data.get("base_nc"), "base_nc") if nc_fijo else None

        if entrada_ya_comp:
            numero = descomplementar(
                numero,
                base_origen,
                separador=separador,
                enteros_totales=enteros_fijos,
                fracc_fijas=fracc_fijas,
            )
            complemento = None

        aviso = "Entrada complementada detectada. Se ajustaron las opciones necesarias." if entrada_ya_comp else None

        min_precision_exacta = _precision_minima_exacta(numero, base_origen, base_dest)
        respetar_precision_objetivo = nc_fijo or entrada_ya_comp
        if redondear:
            precision_base = fracc_fijas if fracc_fijas is not None else precision
            precision_obj = precision_base if respetar_precision_objetivo else max(precision_base, min_precision_exacta)
        else:
            precision_obj = 16 if respetar_precision_objetivo else max(16, min_precision_exacta)

        enteros_valor_fijos = (
            enteros_fijos - 1
            if enteros_fijos is not None and complemento and base_dest == nc_base_fija
            else None
        )

        resultado = convertir(
            numero,
            base_origen,
            base_dest,
            precision=precision_obj,
            complemento=complemento,
            bits_complemento=None,
            separador=separador,
            enteros_valor_fijos=enteros_valor_fijos,
        )
        resultado = _ajustar_salida_fraccion_binaria(resultado, numero, base_origen, base_dest, separador)
        resultado = _quitar_fraccion_si_entero(resultado, numero, base_origen, separador)

        detalle = _manual_conversion_target(
            numero,
            base_origen,
            base_dest,
            separador,
            precision_obj,
            complemento,
            enteros_valor_fijos,
            resultado,
        )
        detalle_data = _manual_conversion_target_data(
            numero,
            base_origen,
            base_dest,
            separador,
            resultado,
            entrada_original=entrada_original,
            entrada_ya_comp=entrada_ya_comp,
            redondear=redondear,
            precision_ui=precision,
            precision_obj=precision_obj,
            min_precision_exacta=min_precision_exacta,
            nc_fijo=nc_fijo,
            fracc_fijas=fracc_fijas,
            complemento=bool(complemento),
        )

        return jsonify({
            "ok": True,
            "target": target,
            "resultado": resultado,
            "detalle": detalle,
            "detalle_data": detalle_data,
            "aviso": aviso,
        })
    except ConversionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/nc2nc")
def api_nc2nc():
    data = request.get_json(force=True)
    try:
        resultado = convertir_nc_a_nc(
            data.get("numero_comp", ""),
            _to_int(data.get("base_origen"), "base_origen"),
            _to_int(data.get("e_origen"), "e_origen"),
            _to_int(data.get("f_origen"), "f_origen"),
            _to_int(data.get("base_destino"), "base_destino"),
            _to_int(data.get("e_destino"), "e_destino"),
            _to_int(data.get("f_destino"), "f_destino"),
            separador=data.get("separador", ","),
        )
        return jsonify({"ok": True, "resultado": resultado})
    except ConversionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/nc2cs")
def api_nc2cs():
    data = request.get_json(force=True)
    try:
        separador = data.get("separador", ",")
        explicito = descomplementar(
            data.get("numero_comp", ""),
            _to_int(data.get("base"), "base"),
            separador=separador,
            enteros_totales=_to_int(data.get("e"), "e"),
            fracc_fijas=_to_int(data.get("f"), "f"),
        )
        resultado = _explicito_a_cs_signo_bit(
            explicito,
            _to_int(data.get("e"), "e"),
            _to_int(data.get("f"), "f"),
            separador,
        )
        return jsonify({"ok": True, "resultado": resultado, "explicito": explicito})
    except ConversionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/suma-nc")
def api_suma_nc():
    data = request.get_json(force=True)
    try:
        resultado = operar_nc_didactico(
            data.get("n1", ""),
            data.get("n2", ""),
            _to_int(data.get("base"), "base"),
            _to_int(data.get("e"), "e"),
            _to_int(data.get("f"), "f"),
            operacion=data.get("operacion", "suma"),
            separador=data.get("separador", ","),
        )
        return jsonify({"ok": True, "resultado": resultado})
    except ConversionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/manual")
def api_manual():
    data = request.get_json(force=True)
    try:
        numero = str(data.get("numero", "")).strip().upper()
        if not numero or numero in ("+", "-"):
            raise ConversionError("Escribe un valor de entrada.")

        base_origen = _to_int(data.get("base_origen"), "base_origen")
        base_dest = _to_int(data.get("base_destino"), "base_destino")
        separador = data.get("separador", ",")
        redondear = bool(data.get("redondear", True))
        precision_ui = _to_int(data.get("precision", 4), "precision")
        entrada_ya_comp = bool(data.get("entrada_complementada", False))
        nc_fijo = bool(data.get("nc_fijo", False))
        complemento_activo = bool(data.get("complemento", False))

        enteros_fijos = _to_int(data.get("e"), "e") if nc_fijo else None
        fracc_fijas = _to_int(data.get("f"), "f") if nc_fijo else None
        nc_base_fija = _to_int(data.get("base_nc"), "base_nc") if nc_fijo else None

        detalle = []
        detalle.append("RESOLUCION MANUAL DEL CONVERSOR")
        detalle.append("")
        detalle.append(f"Entrada: {numero} (base {base_origen})")
        detalle.append(f"Base destino elegida: {base_dest}")
        detalle.append(
            "Opciones: "
            f"redondear={'SI' if redondear else 'NO'}, "
            f"valor_ya_complementado={'SI' if entrada_ya_comp else 'NO'}, "
            f"aplicar_complemento={'SI' if complemento_activo else 'NO'}, "
            f"NC_fijo={'SI' if nc_fijo else 'NO'}"
        )
        if nc_fijo:
            detalle.append(f"NC fijo configurado: (B,E,F)=({nc_base_fija},{enteros_fijos},{fracc_fijas})")

        numero_trabajo = numero
        complemento = "complemento" if complemento_activo else None

        if entrada_ya_comp:
            detalle.append("")
            detalle.append("1) La entrada ya esta complementada, se descomplementa antes de convertir.")
            numero_trabajo, trazas_descomp = _pasos_descomplementar(
                numero_trabajo,
                base_origen,
                enteros_fijos,
                fracc_fijas,
                separador,
            )
            detalle.extend("   " + ln for ln in trazas_descomp)
            complemento = None
        else:
            detalle.append("")
            detalle.append("1) La entrada se toma como valor explicito (no complementado).")

        detalle.append("")
        detalle.append("2) Se expande el numero en forma posicional para obtener su valor decimal exacto:")
        for ln in _pasos_expansion_posicional(numero_trabajo, base_origen):
            detalle.append("   " + ln)

        valor_decimal = _a_decimal(numero_trabajo, base_origen)
        valor_abs = -valor_decimal if valor_decimal < 0 else valor_decimal

        min_precision = _precision_minima_exacta(numero_trabajo, base_origen, base_dest)
        respetar_objetivo = nc_fijo or entrada_ya_comp
        if redondear:
            precision_base = fracc_fijas if fracc_fijas is not None else precision_ui
            precision_obj = precision_base if respetar_objetivo else max(precision_base, min_precision)
            detalle.append("")
            detalle.append("3) Precision de trabajo (fraccion en base destino):")
            detalle.append(f"   precision_base={precision_base}, precision_minima_exacta={min_precision}")
            detalle.append(f"   precision_objetivo={precision_obj}")
        else:
            precision_obj = 16 if respetar_objetivo else max(16, min_precision)
            detalle.append("")
            detalle.append("3) Redondeo desactivado, se usa precision alta de trabajo.")
            detalle.append(f"   precision_objetivo={precision_obj}")

        enteros_valor_fijos = (
            enteros_fijos - 1
            if enteros_fijos is not None and complemento and base_dest == nc_base_fija
            else None
        )

        detalle.append("")
        detalle.append("4) Conversion al destino (calculo numerico):")
        detalle.append(f"   |V| = {_fmt_fraction(valor_abs)}")
        escala = base_dest ** precision_obj
        escalado = valor_abs * escala
        q, r = divmod(escalado.numerator, escalado.denominator)
        detalle.append(f"   escala = B_dest^p = {base_dest}^{precision_obj} = {escala}")
        detalle.append(f"   |V|*escala = {_fmt_fraction(escalado)}")
        detalle.append(f"   Division para redondeo: q={q}, r={r}, denom={escalado.denominator}")
        if r * 2 >= escalado.denominator:
            detalle.append("   Regla half-up: 2*r >= denom, entonces q = q + 1")
        else:
            detalle.append("   Regla half-up: 2*r < denom, entonces q se mantiene")

        entero_redondeado, frac_redondeada = _redondear_absoluto_en_base(valor_abs, base_dest, precision_obj)
        detalle.append(
            f"   Digitos redondeados en base destino: {entero_redondeado}{separador if frac_redondeada else ''}{frac_redondeada}"
        )

        if complemento and str(numero_trabajo).startswith("-"):
            detalle.append("   Como el valor es negativo y aplicar complemento=SI, se codifica en Cn en la base destino.")
        elif complemento:
            detalle.append("   Aplicar complemento esta activo, pero el valor no es negativo, por lo que se conserva explicito.")
        else:
            detalle.append("   Sin complemento en salida, se conserva notacion explicita.")

        if enteros_valor_fijos is not None:
            detalle.append(f"   Se fuerza longitud fija de enteros para valor: {enteros_valor_fijos} digitos.")

        salida = convertir(
            numero_trabajo,
            base_origen,
            base_dest,
            precision=precision_obj,
            complemento=complemento,
            bits_complemento=None,
            separador=separador,
            enteros_valor_fijos=enteros_valor_fijos,
        )
        salida = _ajustar_salida_fraccion_binaria(salida, numero_trabajo, base_origen, base_dest, separador)

        detalle.append("")
        detalle.append("5) Resultado final:")
        detalle.append(f"   Base {base_dest} = {salida}")

        return jsonify({"ok": True, "resultado": salida, "detalle": "\n".join(detalle)})
    except ConversionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
