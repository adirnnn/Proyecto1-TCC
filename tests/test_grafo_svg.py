"""pruebas del incremento 9: generación de grafos SVG (y DOT)."""

import os
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import contexto  # noqa: F401

from grafo_svg import (a_dot, a_svg, exportar_afd, exportar_afn,
                       exportar_grafo, grafo_de_afd, grafo_de_afn,
                       nombre_seguro)
from minimizacion import afd_minimo_de_expresion
from subconjuntos import afd_de_expresion
from thompson import afn_de_expresion


def svg_afn(expresion, titulo=""):
    return a_svg(grafo_de_afn(afn_de_expresion(expresion), titulo))


def svg_afd(expresion, titulo=""):
    return a_svg(grafo_de_afd(afd_de_expresion(expresion), titulo))


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
            # sin mockear `dot`: en esta máquina de pruebas puede estar
            # instalado o no; de cualquier forma el svg y el dot son
            # obligatorios y el png es opcional (None si no hay graphviz).
            ruta_svg, ruta_dot, ruta_png = exportar_afn(
                afn_de_expresion("(a|b)*abb"), base)
            self.assertTrue(os.path.exists(ruta_svg))
            self.assertTrue(os.path.exists(ruta_dot))
            if ruta_png is not None:
                self.assertTrue(os.path.exists(ruta_png))
            with open(ruta_svg, encoding="utf-8") as archivo:
                ET.fromstring(archivo.read())

    def test_sin_graphviz_instalado_no_hay_png_pero_si_svg_y_dot(self):
        with tempfile.TemporaryDirectory() as carpeta, \
             patch("subprocess.run", side_effect=FileNotFoundError):
            base = os.path.join(carpeta, "afd")
            ruta_svg, ruta_dot, ruta_png = exportar_afd(
                afd_de_expresion("a|b"), base)
            self.assertTrue(os.path.exists(ruta_svg))
            self.assertTrue(os.path.exists(ruta_dot))
            self.assertIsNone(ruta_png)

    def test_con_graphviz_simulado_si_hay_png(self):
        salida_falsa = subprocess.CompletedProcess(
            args=["dot"], returncode=0, stdout=b"contenido-png-simulado")
        with tempfile.TemporaryDirectory() as carpeta, \
             patch("subprocess.run", return_value=salida_falsa):
            base = os.path.join(carpeta, "afn")
            ruta_svg, ruta_dot, ruta_png = exportar_afn(
                afn_de_expresion("a"), base)
            self.assertIsNotNone(ruta_png)
            self.assertTrue(os.path.exists(ruta_png))
            with open(ruta_png, "rb") as archivo:
                self.assertEqual(archivo.read(), b"contenido-png-simulado")

    def test_con_graphviz_da_error_no_hay_png_pero_si_svg_y_dot(self):
        salida_falsa = subprocess.CompletedProcess(
            args=["dot"], returncode=1, stdout=b"")
        with tempfile.TemporaryDirectory() as carpeta, \
             patch("subprocess.run", return_value=salida_falsa):
            base = os.path.join(carpeta, "afd_min")
            ruta_svg, ruta_dot, ruta_png = exportar_grafo(
                grafo_de_afn(afn_de_expresion("a"), ""), base)
            self.assertTrue(os.path.exists(ruta_svg))
            self.assertIsNone(ruta_png)

    def test_con_graphviz_false_no_lo_intenta(self):
        with tempfile.TemporaryDirectory() as carpeta, \
             patch("subprocess.run") as llamada:
            base = os.path.join(carpeta, "afn")
            exportar_afn(afn_de_expresion("a"), base, con_graphviz=False)
            llamada.assert_not_called()


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
