from pathlib import Path
import sys

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from conversor import (  # noqa: E402
    ConversionError,
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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
