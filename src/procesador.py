"""fase 7: orquesta el pipeline completo para cada línea del archivo.

este módulo **no imprime nada**: arma objetos ``ResultadoExpresion`` que
``main.py`` se encarga de mostrar. así la lógica queda separada de la interfaz.

formato del archivo de entrada (una expresión por línea):

    (a|b)*abb(a|b)*                 <- solo la expresión; w se pasa con -w
    (a|b)*abb(a|b)*;babbaaaa,abb    <- expresión ; cadenas de prueba por coma
    # esto es un comentario          <- se ignora
                                     <- las líneas vacías se ignoran

reglas:

* las líneas vacías o con solo espacios se **omiten** (no son un error);
* las que empiezan con ``#`` son comentarios y también se omiten;
* se toleran los finales de línea de windows (``\\r\\n``) y un archivo sin
  salto de línea final;
* el **primer** ``;`` de la línea separa la expresión de las cadenas de prueba;
  una cadena vacía entre comas (o al final) significa la **cadena vacía**;
* si una línea falla, se **reporta** y se sigue con las demás.

limitación conocida: como ``;`` separa la expresión de las cadenas, no se puede
usar ``;`` como símbolo del alfabeto dentro del archivo. si se necesita, se pasa
la cadena con ``-w`` y se deja la línea sin ``;``.
"""

import os

from errores import ErrorArchivo, ErrorProyecto
from grafo_svg import exportar_afd, exportar_afn, nombre_seguro
from minimizacion import minimizar
from shunting_yard import convertir, postfix_a_texto
from simulador import respuesta, simular_afd, simular_afn
from subconjuntos import afn_a_afd
from thompson import construir_afn
from tokenizador import SIMBOLO, tokenizar

SEPARADOR_CADENAS = ";"
MARCA_COMENTARIO = "#"


# --------------------------------------------------------------------------
# resultados
# --------------------------------------------------------------------------
class ResultadoSimulacion:
    """resultado de correr una cadena ``w`` en los tres autómatas."""

    def __init__(self, cadena, afn, afd, minimo):
        self.cadena = cadena
        self.afn = afn            # (acepta, pasos)
        self.afd = afd
        self.minimo = minimo

    @property
    def acepta(self):
        return self.afn[0]

    @property
    def coinciden(self):
        """los tres deben dar el mismo veredicto; si no, hay un error."""
        return self.afn[0] == self.afd[0] == self.minimo[0]

    @property
    def respuesta(self):
        return respuesta(self.acepta)


class ResultadoExpresion:
    """todo lo que el programa produjo para una expresión regular."""

    def __init__(self, indice, expresion):
        self.indice = indice
        self.expresion = expresion
        self.postfix = None
        self.afn = None
        self.afd = None
        self.afd_minimo = None
        self.alfabeto = set()
        self.imagenes = {}        # {'afn': (svg, dot), 'afd': ..., 'afd_minimo': ...}
        self.simulaciones = []
        self.error = None

    @property
    def hubo_error(self):
        return self.error is not None


# --------------------------------------------------------------------------
# lectura del archivo
# --------------------------------------------------------------------------
def leer_lineas(ruta):
    """devuelve ``[(numero_de_linea, texto)]`` omitiendo vacías y comentarios."""
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
        if texto.lstrip().startswith(MARCA_COMENTARIO):
            continue
        lineas.append((numero, texto))
    return lineas


def separar_expresion_y_cadenas(linea):
    """divide ``'regex;w1,w2'`` en ``('regex', ['w1', 'w2'])``.

    sin ``;`` no hay cadenas.  ``'regex;'`` da lista vacía; una cadena vacía
    entre comas -o al final- es la cadena vacía.
    """
    if SEPARADOR_CADENAS in linea:
        expresion, resto = linea.split(SEPARADOR_CADENAS, 1)
        cadenas = resto.split(",") if resto != "" else []
        return expresion.strip(), cadenas
    return linea.strip(), []


# --------------------------------------------------------------------------
# pipeline de una expresión
# --------------------------------------------------------------------------
def construir_automatas(expresion):
    """``regex`` -> ``(postfix_tokens, AFN, AFD, AFD_minimo)``."""
    postfix = convertir(tokenizar(expresion))
    afn = construir_afn(postfix)
    afd = afn_a_afd(afn)
    return postfix, afn, afd, minimizar(afd)


def _alfabeto_de_postfix(postfix):
    """símbolos del alfabeto que aparecen en la expresión (sin ε)."""
    from simbolos import EPSILON
    return {t.valor for t in postfix if t.tipo == SIMBOLO and t.valor is not EPSILON}


def simular_en_los_tres(resultado, cadena):
    """corre ``cadena`` en el AFN, el AFD y el AFD mínimo y guarda el resultado."""
    simulacion = ResultadoSimulacion(
        cadena,
        simular_afn(resultado.afn, cadena),
        simular_afd(resultado.afd, cadena),
        simular_afd(resultado.afd_minimo, cadena))
    resultado.simulaciones.append(simulacion)
    return simulacion


def procesar_expresion(indice, expresion, cadenas=(), carpeta_salida=None,
                       generar_imagenes=True):
    """ejecuta el pipeline completo de una expresión y devuelve su
    ``ResultadoExpresion`` (un error previsible queda guardado en ``.error``).
    """
    resultado = ResultadoExpresion(indice, expresion)
    try:
        postfix, afn, afd, minimo = construir_automatas(expresion)
        resultado.postfix = postfix_a_texto(postfix)
        resultado.afn = afn
        resultado.afd = afd
        resultado.afd_minimo = minimo
        resultado.alfabeto = _alfabeto_de_postfix(postfix)

        if generar_imagenes and carpeta_salida:
            base = os.path.join(carpeta_salida,
                                "%02d_%s" % (indice, nombre_seguro(expresion)))
            resultado.imagenes["afn"] = exportar_afn(
                afn, os.path.join(base, "afn"),
                "AFN (Thompson) - %s" % expresion)
            resultado.imagenes["afd"] = exportar_afd(
                afd, os.path.join(base, "afd_subconjuntos"),
                "AFD (subconjuntos) - %s" % expresion)
            resultado.imagenes["afd_minimo"] = exportar_afd(
                minimo, os.path.join(base, "afd_minimizado"),
                "AFD minimizado - %s" % expresion)

        for cadena in cadenas:
            simular_en_los_tres(resultado, cadena)
    except ErrorProyecto as error:
        resultado.error = error
    return resultado


def procesar_expresiones(expresiones, cadenas_globales=(), carpeta_salida=None,
                         generar_imagenes=True, inicio=1):
    """procesa expresiones que llegan sueltas (las que se pasan con ``-r``).

    a diferencia de las líneas del archivo, aquí el texto se toma **tal cual**:
    ni ``;`` separa cadenas de prueba ni ``#`` empieza un comentario, así que
    los dos pueden usarse como símbolos del alfabeto.
    """
    return [procesar_expresion(indice, expresion, list(cadenas_globales),
                               carpeta_salida, generar_imagenes)
            for indice, expresion in enumerate(expresiones, start=inicio)]


def procesar_archivo(ruta, cadenas_globales=(), carpeta_salida=None,
                     generar_imagenes=True, inicio=1):
    """procesa cada línea del archivo de forma independiente.

    un error en una línea **no** detiene el procesamiento de las demás: queda
    guardado en ``resultado.error``.  ``inicio`` es el número que lleva la
    primera expresión (sirve para seguir la cuenta después de las de ``-r``).
    """
    resultados = []
    for indice, (_, linea) in enumerate(leer_lineas(ruta), start=inicio):
        expresion, cadenas = separar_expresion_y_cadenas(linea)
        if not cadenas:
            cadenas = list(cadenas_globales)
        resultados.append(procesar_expresion(
            indice, expresion, cadenas, carpeta_salida, generar_imagenes))
    return resultados
