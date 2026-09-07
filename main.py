"""proyecto 1 - teoría de la computación.

de una expresión regular en notación infija a:

  infix --(shunting yard)--> postfix --(thompson)--> AFN
        --(subconjuntos)--> AFD --(minimización)--> AFD mínimo

y simulación de una cadena ``w`` en los tres autómatas para responder **sí** /
**no** según si ``w`` pertenece al lenguaje de la expresión.

el programa lee un archivo de texto con **una expresión regular por línea** y
procesa todas. una línea con error se reporta y no detiene a las demás.

uso:

    python main.py expresiones.txt -w babbaaaa
    python main.py expresiones.txt -w abb -w ""        (cadena vacía)
    python main.py expresiones.txt --sin-imagenes --detalle
    python main.py expresiones.txt -s imagenes --tabla

si no se pasa ``-w`` y la línea no trae sus propias cadenas (tras ``;``), el
programa pide la cadena por teclado.

códigos de salida: 0 todo bien · 1 alguna línea con error o desacuerdo entre
autómatas · 2 no se pudo leer el archivo.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from errores import ErrorProyecto  # noqa: E402
from procesador import leer_lineas, procesar_archivo  # noqa: E402,F401
from simulador import SI  # noqa: E402

ANCHO = 74


def preparar_consola_utf8():
    """evita que la consola de windows falle al imprimir ``ε``."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _mostrar_cadena(cadena):
    return "ε (cadena vacía)" if cadena == "" else '"%s"' % cadena


def _imprimir_encabezado(resultado):
    print("=" * ANCHO)
    print("expresión %d (infix): %s" % (resultado.indice, resultado.expresion))
    print("-" * ANCHO)


def _imprimir_automatas(resultado, con_tabla):
    print("postfix : %s" % resultado.postfix)
    print("alfabeto: {%s}" % ", ".join(sorted(resultado.alfabeto)))
    print(resultado.afn.resumen())
    print(resultado.afd.resumen().replace("AFD:", "AFD (subconjuntos):"))
    print(resultado.afd_minimo.resumen().replace("AFD:", "AFD (minimizado)  :"))
    if con_tabla:
        print("\ntabla del AFD por subconjuntos:")
        print(resultado.afd.tabla())
        print("\ntabla del AFD minimizado:")
        print(resultado.afd_minimo.tabla())


def _imprimir_imagenes(resultado):
    if not resultado.imagenes:
        return
    print("\ngrafos generados:")
    etiquetas = {"afn": "AFN             ",
                 "afd": "AFD subconjuntos",
                 "afd_minimo": "AFD minimizado  "}
    for clave in ("afn", "afd", "afd_minimo"):
        ruta_svg, ruta_dot = resultado.imagenes[clave]
        print("  %s -> %s  (+ %s)" % (etiquetas[clave], ruta_svg,
                                      os.path.basename(ruta_dot)))


def _imprimir_simulaciones(resultado, con_detalle):
    if not resultado.simulaciones:
        print("\n(no se indicó ninguna cadena w para esta expresión)")
        return
    for simulacion in resultado.simulaciones:
        print("\nsimulando w = %s" % _mostrar_cadena(simulacion.cadena))
        for etiqueta, (acepta, pasos) in (
                ("AFN             ", simulacion.afn),
                ("AFD subconjuntos", simulacion.afd),
                ("AFD minimizado  ", simulacion.minimo)):
            print("  %s: %s" % (etiqueta, SI if acepta else "no"))
            if con_detalle:
                for paso in pasos:
                    print("      %s" % paso)
        if not simulacion.coinciden:
            print("  *** ATENCIÓN: los autómatas NO coinciden (hay un error) ***")
        print("  => w %s pertenece a L(r):  %s"
              % ("SÍ" if simulacion.acepta else "NO",
                 simulacion.respuesta.upper()))


def _imprimir_resultado(resultado, con_detalle, con_tabla):
    _imprimir_encabezado(resultado)
    if resultado.hubo_error:
        print("ERROR: %s" % resultado.error)
        print()
        return
    _imprimir_automatas(resultado, con_tabla)
    _imprimir_imagenes(resultado)
    _imprimir_simulaciones(resultado, con_detalle)
    print()


def _pedir_cadena_interactiva():
    """pide ``w`` por teclado.  devuelve ``None`` si no hay terminal."""
    if not sys.stdin or not sys.stdin.isatty():
        return None
    try:
        return input("ingrese la cadena w a evaluar (ENTER = cadena vacía): ")
    except EOFError:
        return None


def construir_argumentos():
    analizador = argparse.ArgumentParser(
        description="proyecto 1 de teoría de la computación: expresiones "
                    "regulares -> afn (thompson) -> afd (subconjuntos) -> afd "
                    "mínimo.")
    analizador.add_argument(
        "archivo", help="archivo de texto con una expresión regular por línea")
    analizador.add_argument(
        "-w", "--cadena", action="append", default=[], metavar="W",
        help="cadena w a evaluar (se puede repetir: -w abb -w ba)")
    analizador.add_argument(
        "-s", "--salida", default="salida", metavar="CARPETA",
        help="carpeta donde se guardan los grafos (por defecto: salida)")
    analizador.add_argument(
        "--sin-imagenes", action="store_true",
        help="no generar los archivos SVG ni DOT")
    analizador.add_argument(
        "-d", "--detalle", action="store_true",
        help="mostrar la traza paso a paso de cada simulación")
    analizador.add_argument(
        "-t", "--tabla", action="store_true",
        help="mostrar las tablas de transiciones de los AFD")
    return analizador


def main(argv=None):
    preparar_consola_utf8()
    argumentos = construir_argumentos().parse_args(argv)

    cadenas = list(argumentos.cadena)
    if not cadenas:
        interactiva = _pedir_cadena_interactiva()
        if interactiva is not None:
            cadenas = [interactiva]

    try:
        resultados = procesar_archivo(
            argumentos.archivo,
            cadenas_globales=cadenas,
            carpeta_salida=None if argumentos.sin_imagenes else argumentos.salida,
            generar_imagenes=not argumentos.sin_imagenes)
    except ErrorProyecto as error:
        print("error: %s" % error, file=sys.stderr)
        return 2

    for resultado in resultados:
        _imprimir_resultado(resultado, argumentos.detalle, argumentos.tabla)

    con_error = [r for r in resultados if r.hubo_error]
    desacuerdos = [r for r in resultados
                   if not r.hubo_error
                   and any(not s.coinciden for s in r.simulaciones)]

    print("=" * ANCHO)
    if not resultados:
        print("el archivo no contiene ninguna expresión regular.")
        return 0
    print("resumen: %d expresiones procesadas, %d con error."
          % (len(resultados), len(con_error)))
    if desacuerdos:
        print("ATENCIÓN: %d expresiones donde los autómatas no coincidieron."
              % len(desacuerdos))
    return 1 if (con_error or desacuerdos) else 0


if __name__ == "__main__":
    sys.exit(main())
