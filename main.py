"""proyecto 1 - teoría de la computación.

de una expresión regular a un afn (thompson), a un afd (subconjuntos), a un afd
mínimo, y simulación de una cadena ``w`` en los tres.

por ahora (incremento 1) este archivo solo lee el archivo de expresiones y
muestra las líneas que se van a procesar (una expresión regular por línea). en
los siguientes incrementos se agregan las etapas: shunting yard, thompson,
subconjuntos, minimización y simulación.

uso:

    python main.py expresiones.txt
    python main.py expresiones.txt -w babbaaaa -w abb
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from errores import ErrorArchivo  # noqa: E402


def preparar_consola_utf8():
    """evita que la consola de windows falle al imprimir ``ε`` más adelante."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def leer_lineas(ruta):
    """devuelve ``[(numero_de_linea, texto)]`` omitiendo vacías y comentarios.

    reglas: las líneas vacías o con solo espacios se omiten (no son un error);
    las que empiezan con ``#`` son comentarios y también se omiten. se toleran
    los finales de línea de windows (``\\r\\n``) y un archivo sin salto final.
    """
    if not os.path.exists(ruta):
        raise ErrorArchivo("no existe el archivo: %s" % ruta)
    if os.path.isdir(ruta):
        raise ErrorArchivo("la ruta es una carpeta, no un archivo: %s" % ruta)

    try:
        with open(ruta, "r", encoding="utf-8", newline="") as archivo:
            crudas = archivo.read().splitlines()
    except UnicodeDecodeError:
        raise ErrorArchivo(
            "el archivo %s no está en utf-8; guárdalo en utf-8 para poder leer "
            "símbolos como ε." % ruta)
    except OSError as detalle:
        raise ErrorArchivo("no se pudo leer %s: %s" % (ruta, detalle))

    lineas = []
    for numero, cruda in enumerate(crudas, start=1):
        texto = cruda.rstrip("\r")
        if not texto.strip():
            continue
        if texto.lstrip().startswith("#"):
            continue
        lineas.append((numero, texto))
    return lineas


def construir_argumentos():
    analizador = argparse.ArgumentParser(
        description="proyecto 1 de teoría de la computación: expresiones "
                    "regulares -> afn (thompson) -> afd (subconjuntos) -> afd "
                    "mínimo.")
    analizador.add_argument(
        "archivo",
        help="archivo de texto con una expresión regular por línea")
    analizador.add_argument(
        "-w", "--cadena", action="append", default=[], metavar="W",
        help="cadena w a evaluar (se puede repetir: -w abb -w ba)")
    return analizador


def main(argv=None):
    preparar_consola_utf8()
    argumentos = construir_argumentos().parse_args(argv)

    try:
        lineas = leer_lineas(argumentos.archivo)
    except ErrorArchivo as error:
        print("error: %s" % error, file=sys.stderr)
        return 2

    if not lineas:
        print("el archivo no contiene ninguna expresión regular.")
        return 0

    print("expresiones encontradas: %d" % len(lineas))
    for indice, (numero, texto) in enumerate(lineas, start=1):
        print("  %2d (línea %d del archivo): %s" % (indice, numero, texto))

    if argumentos.cadena:
        print("cadenas w recibidas: %s"
              % ", ".join(repr(cadena) for cadena in argumentos.cadena))
    else:
        print("(todavía no se indicó ninguna cadena w)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
