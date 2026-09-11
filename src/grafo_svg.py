"""fase 6: dibujar el AFN y los AFD.

los algoritmos no saben dibujar. el flujo es:

    AFN / AFD  ->  Grafo (modelo neutro)  ->  texto SVG   (imagen, siempre)
                                          ->  texto DOT   (siempre)
                                          ->  imagen PNG  (con Graphviz, si está)

el SVG se genera **a mano** con la biblioteca estándar: no hace falta instalar
nada, y **siempre** se produce, aunque Graphviz no esté disponible. el acomodo
es por niveles BFS desde el inicial (una columna por nivel) y reparto vertical
dentro de la columna: es sencillo -para autómatas grandes (20+ estados) queda
apretado y algunas aristas se cruzan- pero es determinista y nunca falla.

si el binario `dot` de Graphviz está instalado y en el PATH, **además** se
genera un `.png` a partir del mismo `.dot` -con mejor acomodo automático,
sobre todo para autómatas grandes-. no es obligatorio: si `dot` no está, el
programa simplemente no genera el PNG y se queda con el SVG. no se agrega
ninguna dependencia de Python nueva: se invoca `dot` como proceso externo
(``subprocess``), no se importa el paquete ``graphviz`` de PyPI.

convenciones que pide el enunciado (las cumplen los tres formatos):

* el **estado inicial** se marca con una flecha que viene de la nada;
* los **estados de aceptación** se dibujan con doble círculo;
* cada **transición** lleva su símbolo (ε incluido); las transiciones paralelas
  entre los mismos dos estados se juntan en una sola arista con las etiquetas
  separadas por coma; los auto-lazos se dibujan como un arco sobre el estado.
"""

import math
import os
import subprocess

from simbolos import EPSILON
from tokenizador import mostrar_valor

RADIO = 22
DX = 120          # separación horizontal entre niveles
DY = 84           # separación vertical entre estados de un mismo nivel
MARGEN = 40
MARGEN_IZQ = 90   # espacio extra a la izquierda para la flecha de "inicio"
CURVA = 26        # cuánto se arquean las aristas (para que ida y vuelta no se pisen)


# ==========================================================================
# modelo neutro
# ==========================================================================
class Grafo:
    """grafo dirigido y etiquetado que el renderizador sabe dibujar."""

    def __init__(self, titulo=""):
        self.titulo = titulo
        self.nodos = []            # nombres, en orden de dibujo
        self.inicial = None
        self.aceptacion = set()
        self.aristas = {}          # {(origen, destino): [etiquetas]}

    def agregar_nodo(self, nombre, es_inicial=False, es_aceptacion=False):
        self.nodos.append(nombre)
        if es_inicial:
            self.inicial = nombre
        if es_aceptacion:
            self.aceptacion.add(nombre)

    def agregar_arista(self, origen, destino, etiqueta):
        etiquetas = self.aristas.setdefault((origen, destino), [])
        if etiqueta not in etiquetas:
            etiquetas.append(etiqueta)

    def etiqueta_de(self, origen, destino):
        return ", ".join(self.aristas[(origen, destino)])


def _etiqueta_afn(transicion):
    return "ε" if transicion.es_epsilon else mostrar_valor(transicion.simbolo)


def grafo_de_afn(afn, titulo=""):
    grafo = Grafo(titulo)
    for estado in afn.estados:
        grafo.agregar_nodo(estado.nombre,
                           es_inicial=(estado is afn.inicial),
                           es_aceptacion=afn.es_aceptacion(estado))
    for transicion in afn.transiciones():
        grafo.agregar_arista(transicion.origen.nombre, transicion.destino.nombre,
                             _etiqueta_afn(transicion))
    return grafo


def grafo_de_afd(afd, titulo=""):
    grafo = Grafo(titulo)
    for estado in afd.estados:
        grafo.agregar_nodo(afd.nombre(estado),
                           es_inicial=(estado == afd.inicial),
                           es_aceptacion=afd.es_aceptacion(estado))
    for origen, simbolo, destino in afd.transiciones_ordenadas():
        grafo.agregar_arista(afd.nombre(origen), afd.nombre(destino),
                             mostrar_valor(simbolo))
    return grafo


# ==========================================================================
# acomodo
# ==========================================================================
def _niveles_bfs(grafo):
    """distancia (en aristas) de cada nodo al inicial; los no alcanzados van al 0."""
    niveles = {}
    if grafo.inicial is not None:
        niveles[grafo.inicial] = 0
        cola = [grafo.inicial]
        while cola:
            actual = cola.pop(0)
            for (origen, destino) in grafo.aristas:
                if origen == actual and destino not in niveles:
                    niveles[destino] = niveles[actual] + 1
                    cola.append(destino)
    for nombre in grafo.nodos:
        niveles.setdefault(nombre, 0)
    return niveles


def _posiciones(grafo):
    """asigna a cada nodo un (x, y) en píxeles."""
    niveles = _niveles_bfs(grafo)
    por_nivel = {}
    for nombre in grafo.nodos:
        por_nivel.setdefault(niveles[nombre], []).append(nombre)

    altura_max = max((len(col) for col in por_nivel.values()), default=1)
    posiciones = {}
    for nivel, columna in por_nivel.items():
        arranque = (altura_max - len(columna)) / 2.0
        for fila, nombre in enumerate(columna):
            x = MARGEN_IZQ + nivel * DX + RADIO
            y = MARGEN + (arranque + fila) * DY + RADIO
            posiciones[nombre] = (x, y)

    ancho = MARGEN_IZQ + (max(niveles.values()) + 1) * DX + MARGEN
    alto = MARGEN * 2 + altura_max * DY
    return posiciones, ancho, alto


# ==========================================================================
# SVG
# ==========================================================================
def _xml(texto):
    return (texto.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _arco(x1, y1, x2, y2):
    """path de una arista curva entre dos estados distintos y el punto medio del
    arco (para colocar la etiqueta)."""
    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    dx, dy = x2 - x1, y2 - y1
    largo = math.hypot(dx, dy) or 1.0
    # normal (hacia la izquierda del vector origen->destino)
    cx = mx - dy / largo * CURVA
    cy = my + dx / largo * CURVA

    ang1 = math.atan2(cy - y1, cx - x1)
    ang2 = math.atan2(cy - y2, cx - x2)
    sx, sy = x1 + RADIO * math.cos(ang1), y1 + RADIO * math.sin(ang1)
    ex, ey = x2 + RADIO * math.cos(ang2), y2 + RADIO * math.sin(ang2)
    path = "M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (sx, sy, cx, cy, ex, ey)
    return path, (cx, cy - 4)


def _lazo(x, y):
    """path de un auto-lazo sobre el estado y el punto para la etiqueta."""
    path = ("M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f"
            % (x - 8, y - RADIO, x - 46, y - RADIO - 46,
               x + 46, y - RADIO - 46, x + 8, y - RADIO))
    return path, (x, y - RADIO - 40)


def a_svg(grafo):
    """genera el texto SVG del grafo."""
    posiciones, ancho, alto = _posiciones(grafo)
    y0 = 0
    if grafo.titulo:
        y0 = 24
        alto += y0

    partes = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'font-family="Helvetica, Arial, sans-serif" font-size="13">' % (ancho, alto),
        '<defs><marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#333"/></marker></defs>',
        '<rect width="%d" height="%d" fill="white"/>' % (ancho, alto),
    ]
    if grafo.titulo:
        partes.append('<text x="%d" y="16" text-anchor="middle" '
                      'font-weight="bold">%s</text>'
                      % (ancho // 2, _xml(grafo.titulo)))

    grupo = ['<g transform="translate(0,%d)">' % y0]

    # aristas
    for (origen, destino) in grafo.aristas:
        x1, y1 = posiciones[origen]
        x2, y2 = posiciones[destino]
        etiqueta = _xml(grafo.etiqueta_de(origen, destino))
        if origen == destino:
            path, (lx, ly) = _lazo(x1, y1)
        else:
            path, (lx, ly) = _arco(x1, y1, x2, y2)
        grupo.append('<path d="%s" fill="none" stroke="#333" '
                     'marker-end="url(#punta)"/>' % path)
        grupo.append('<rect x="%.1f" y="%.1f" width="%d" height="15" '
                     'fill="white" opacity="0.85"/>'
                     % (lx - 4 * len(etiqueta) - 2, ly - 12,
                        8 * len(etiqueta) + 4))
        grupo.append('<text x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                     % (lx, ly, etiqueta))

    # flecha de "inicio"
    if grafo.inicial is not None:
        xi, yi = posiciones[grafo.inicial]
        grupo.append('<path d="M %.1f %.1f L %.1f %.1f" fill="none" '
                     'stroke="#333" marker-end="url(#punta)"/>'
                     % (xi - RADIO - 34, yi, xi - RADIO - 2, yi))
        grupo.append('<text x="%.1f" y="%.1f" text-anchor="end">inicio</text>'
                     % (xi - RADIO - 38, yi + 4))

    # nodos
    for nombre in grafo.nodos:
        x, y = posiciones[nombre]
        if nombre in grafo.aceptacion:
            grupo.append('<circle class="aceptacion" cx="%.1f" cy="%.1f" r="%d" '
                         'fill="none" stroke="#333"/>' % (x, y, RADIO + 4))
        grupo.append('<circle class="estado" cx="%.1f" cy="%.1f" r="%d" '
                     'fill="#eef4ff" stroke="#333"/>' % (x, y, RADIO))
        grupo.append('<text x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                     % (x, y + 4, _xml(nombre)))

    grupo.append('</g>')
    partes.extend(grupo)
    partes.append('</svg>')
    return "\n".join(partes) + "\n"


# ==========================================================================
# DOT (texto; no se renderiza, es una cortesía por si hay graphviz)
# ==========================================================================
def _dot_id(texto):
    return '"%s"' % texto.replace("\\", "\\\\").replace('"', '\\"')


def a_dot(grafo):
    lineas = ["digraph automata {", "    rankdir=LR;",
              '    node [fontname="Helvetica"];',
              '    edge [fontname="Helvetica"];']
    if grafo.titulo:
        lineas.append('    labelloc="t";')
        lineas.append('    label=%s;' % _dot_id(grafo.titulo))
    lineas.append('    __inicio [shape=point width=0.12 label=""];')
    for nombre in grafo.nodos:
        forma = "doublecircle" if nombre in grafo.aceptacion else "circle"
        lineas.append('    %s [shape=%s];' % (_dot_id(nombre), forma))
    if grafo.inicial is not None:
        lineas.append('    __inicio -> %s;' % _dot_id(grafo.inicial))
    for (origen, destino) in grafo.aristas:
        lineas.append('    %s -> %s [label=%s];'
                      % (_dot_id(origen), _dot_id(destino),
                         _dot_id(grafo.etiqueta_de(origen, destino))))
    lineas.append("}")
    return "\n".join(lineas) + "\n"


# ==========================================================================
# Graphviz (opcional): renderiza el mismo .dot con el binario `dot`
# ==========================================================================
def _renderizar_con_graphviz(texto_dot, ruta_png, formato="png"):
    """intenta invocar el binario `dot` de Graphviz sobre ``texto_dot``.

    devuelve ``True`` y escribe ``ruta_png`` si lo logra; ``False`` si el
    binario no está instalado, no responde, o falla -en cualquier caso no se
    lanza una excepción, porque el SVG a mano ya cubre la generación de la
    imagen-.
    """
    try:
        resultado = subprocess.run(
            ["dot", "-T%s" % formato],
            input=texto_dot.encode("utf-8"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False  # no está instalado el binario `dot`, o no respondió
    if resultado.returncode != 0 or not resultado.stdout:
        return False
    with open(ruta_png, "wb") as archivo:
        archivo.write(resultado.stdout)
    return True


# ==========================================================================
# API de archivos
# ==========================================================================
def exportar_grafo(grafo, ruta_base, con_graphviz=True):
    """escribe ``ruta_base.svg`` y ``ruta_base.dot`` (siempre), y
    ``ruta_base.png`` con Graphviz si ``dot`` está disponible.

    devuelve ``(ruta_svg, ruta_dot, ruta_png)``; ``ruta_png`` es ``None`` si
    Graphviz no estaba instalado o falló al renderizar.
    """
    carpeta = os.path.dirname(ruta_base)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    ruta_svg = ruta_base + ".svg"
    ruta_dot = ruta_base + ".dot"
    texto_dot = a_dot(grafo)
    with open(ruta_svg, "w", encoding="utf-8") as archivo:
        archivo.write(a_svg(grafo))
    with open(ruta_dot, "w", encoding="utf-8") as archivo:
        archivo.write(texto_dot)

    ruta_png = ruta_base + ".png"
    if not (con_graphviz and _renderizar_con_graphviz(texto_dot, ruta_png)):
        ruta_png = None
    return ruta_svg, ruta_dot, ruta_png


def exportar_afn(afn, ruta_base, titulo="AFN (Thompson)", con_graphviz=True):
    return exportar_grafo(grafo_de_afn(afn, titulo), ruta_base, con_graphviz)


def exportar_afd(afd, ruta_base, titulo="AFD", con_graphviz=True):
    return exportar_grafo(grafo_de_afd(afd, titulo), ruta_base, con_graphviz)


def nombre_seguro(texto, maximo=40):
    """convierte una expresión regular en un nombre de carpeta válido."""
    reemplazos = {"|": "-o-", "*": "-est", "+": "-mas", "?": "-opt",
                  "(": "_", ")": "_", " ": "", "\\": "-esc", EPSILON: "epsilon",
                  "ε": "epsilon", "/": "-", ":": "-", ".": "-punto",
                  '"': "", "<": "", ">": ""}
    resultado = "".join(reemplazos.get(c, c) for c in texto)
    resultado = "".join(c for c in resultado if c.isalnum() or c in "-_")
    return resultado.strip("-_")[:maximo] or "expresion"
