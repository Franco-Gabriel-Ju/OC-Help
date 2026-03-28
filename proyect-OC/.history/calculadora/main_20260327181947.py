import argparse

from conversor import ConversionError, convertir


def _crear_parser():
    parser = argparse.ArgumentParser(
        description="Conversor de sistemas numericos (bases 2 a 36)."
    )
    parser.add_argument("numero", help="Numero a convertir. Ej: 1010.11")
    parser.add_argument("base_origen", type=int, help="Base de origen")
    parser.add_argument("base_destino", type=int, help="Base de destino")
    parser.add_argument(
        "--precision",
        type=int,
        default=12,
        help="Cantidad maxima de digitos fraccionarios en la salida",
    )
    return parser


def main():
    parser = _crear_parser()
    args = parser.parse_args()

    try:
        resultado = convertir(
            args.numero,
            args.base_origen,
            args.base_destino,
            precision=args.precision,
        )
    except ConversionError as exc:
        parser.error(str(exc))
        return

    print(resultado)


if __name__ == "__main__":
    main()
