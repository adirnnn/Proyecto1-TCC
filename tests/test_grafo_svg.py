"""pruebas del incremento 9: generación de grafos SVG (y DOT)."""

import os
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET

import contexto  # noqa: F401

from grafo_svg import (ALTO_TITULO, a_dot, a_svg, exportar_afn, grafo_de_afd,
                       grafo_de_afn, nombre_seguro)
from minimizacion import afd_minimo_de_expresion
from subconjuntos import afd_de_expresion
from thompson import afn_de_expresion


def svg_afn(expresion, titulo=""):
    return a_svg(grafo_de_afn(afn_de_expresion(expresion), titulo))


def svg_afd(expresion, titulo=""):
    return a_svg(grafo_de_afd(afd_de_expresion(expresion), titulo))


SVG = "{http://www.w3.org/2000/svg}"


def tope_del_dibujo(svg):
    """la ``y`` más pequeña que se dibuja, ya con el ``translate`` aplicado.

    mira las aristas (``path``) y los recuadros de las etiquetas (``rect``):
    son los que sobresalen por arriba cuando hay un auto-lazo.
    """
    grupo = ET.fromstring(svg).find(SVG + "g")
    desplazamiento = float(
        re.match(r"translate\(0,([-\d.]+)\)", grupo.get("transform")).group(1))
    coordenadas = []
    for elemento in grupo.iter():
        if elemento.tag == SVG + "path":
            numeros = [pieza for pieza in elemento.get("d").split()
                       if pieza not in ("M", "L", "C", "Q", "z")]
            coordenadas.extend(float(n) for n in numeros[1::2])   # las y
        elif elemento.tag == SVG + "rect" and elemento.get("y") is not None:
            coordenadas.append(float(elemento.get("y")))
    return desplazamiento + min(coordenadas)


class PruebasSVGBienFormado(unittest.TestCase):
    def test_es_xml_valido(self):
        for expresion in ("a", "a|b", "a*", "(a|b)*abb(a|b)*", "ε"):
            raiz = ET.fromstring(svg_afn(expresion))
            self.assertTrue(raiz.tag.endswith("svg"), expresion)

    def test_un_circulo_estado_por_nodo(self):
        svg = svg_afn("a")            # AFN de 'a' -> 2 estados
        self.assertEqual(svg.count('class="estado"'), 2)

    def test_doble_circulo_en_los_de_aceptacion(self):
        svg = svg_afn("a")            # exactamente 1 estado de aceptación
        self.assertEqual(svg.count('class="aceptacion"'), 1)

    def test_marca_de_estado_inicial(self):
        self.assertIn(">inicio<", svg_afn("a"))

    def test_etiqueta_epsilon_presente(self):
        # el AFN de 'a*' tiene varias transiciones ε
        self.assertIn(">ε<", svg_afn("a*"))

    def test_titulo_se_incluye(self):
        self.assertIn("mi titulo", svg_afn("a", "mi titulo"))


class PruebasCasosDeAutomata(unittest.TestCase):
    def test_un_solo_estado(self):
        svg = a_svg(grafo_de_afd(afd_minimo_de_expresion("a*"), ""))
        ET.fromstring(svg)
        self.assertEqual(svg.count('class="estado"'), 1)
        self.assertEqual(svg.count('class="aceptacion"'), 1)

    def test_con_ciclo_dibuja_un_auto_lazo(self):
        # el AFD mínimo de '(a|b)*' es un único estado con auto-lazos a y b
        svg = a_svg(grafo_de_afd(afd_minimo_de_expresion("(a|b)*"), ""))
        self.assertIn(" C ", svg)          # un lazo usa una curva cúbica 'C'

    def test_automata_denso_no_rompe(self):
        svg = svg_afn("(a|b)*abb(a|b)*")   # 22 estados
        raiz = ET.fromstring(svg)
        self.assertTrue(raiz.tag.endswith("svg"))

    def test_un_auto_lazo_no_se_sale_del_lienzo(self):
        # el AFD mínimo de '(a|b)*' es un solo estado con auto-lazos: el arco
        # sube por encima del estado y no debe quedar recortado.
        svg = a_svg(grafo_de_afd(afd_minimo_de_expresion("(a|b)*"), ""))
        self.assertGreaterEqual(tope_del_dibujo(svg), 0)

    def test_un_auto_lazo_no_se_cruza_con_el_titulo(self):
        svg = a_svg(grafo_de_afd(afd_minimo_de_expresion("(a|b)*"),
                                 "AFD minimizado"))
        self.assertGreater(tope_del_dibujo(svg), ALTO_TITULO)

    def test_el_lienzo_crece_para_dejar_sitio_al_lazo(self):
        con_lazo = a_svg(grafo_de_afd(afd_minimo_de_expresion("(a|b)*"), ""))
        sin_lazo = a_svg(grafo_de_afn(afn_de_expresion("a"), ""))

        def alto(svg):
            return float(ET.fromstring(svg).get("viewBox").split()[3])

        self.assertGreater(alto(con_lazo), alto(sin_lazo))

    def test_automata_vacio_de_transiciones(self):
        svg = svg_afn("ε")                 # 2 estados, 1 transición ε
        ET.fromstring(svg)
        self.assertIn(">ε<", svg)


class PruebasDOT(unittest.TestCase):
    def test_dot_basico(self):
        dot = a_dot(grafo_de_afn(afn_de_expresion("a|b"), "t"))
        self.assertTrue(dot.startswith("digraph automata {"))
        self.assertIn("doublecircle", dot)
        self.assertIn("__inicio ->", dot)


class PruebasArchivos(unittest.TestCase):
    def test_exportar_afn_escribe_svg_y_dot(self):
        with tempfile.TemporaryDirectory() as carpeta:
            base = os.path.join(carpeta, "afn")
            ruta_svg, ruta_dot = exportar_afn(afn_de_expresion("(a|b)*abb"), base)
            self.assertTrue(os.path.exists(ruta_svg))
            self.assertTrue(os.path.exists(ruta_dot))
            with open(ruta_svg, encoding="utf-8") as archivo:
                ET.fromstring(archivo.read())


class PruebasNombreSeguro(unittest.TestCase):
    def test_quita_metacaracteres(self):
        seguro = nombre_seguro("(a|b)*abb(a|b)*")
        for prohibido in "()|*":
            self.assertNotIn(prohibido, seguro)
        self.assertTrue(seguro)

    def test_epsilon_se_vuelve_palabra(self):
        self.assertIn("epsilon", nombre_seguro("εa"))

    def test_nunca_queda_vacio(self):
        self.assertEqual(nombre_seguro("()"), "expresion")


if __name__ == "__main__":
    unittest.main()
