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
        return jsonify({"ok": True, "resultado": resultado})
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
    app.run(host="127.0.0.1", port=5000, debug=True)
