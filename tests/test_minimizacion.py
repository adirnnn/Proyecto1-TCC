"""pruebas del incremento 8: minimización del AFD (inalcanzables + particiones)."""

import itertools
import unittest

import contexto  # noqa: F401

from automata import AFD
from minimizacion import (afd_minimo_de_expresion, eliminar_inalcanzables,
                          minimizar)
from simulador import acepta_afd, acepta_afn
from subconjuntos import afd_de_expresion
from thompson import afn_de_expresion


def cadenas_hasta(longitud, alfabeto="ab"):
    for n in range(longitud + 1):
        for tupla in itertools.product(alfabeto, repeat=n):
            yield "".join(tupla)


class PruebasInalcanzables(unittest.TestCase):
    def test_elimina_un_estado_sin_camino_desde_el_inicial(self):
        # S2 es inalcanzable
        afd = AFD([0, 1, 2], ["a"], 0, {1},
                  {(0, "a"): 1, (1, "a"): 1, (2, "a"): 2})
        limpio = eliminar_inalcanzables(afd)
        self.assertEqual(len(limpio.estados), 2)

    def test_conserva_el_lenguaje(self):
        afd = afd_de_expresion("(a|b)*abb")
        minimo = minimizar(afd)
        for cadena in cadenas_hasta(6):
            self.assertEqual(acepta_afd(afd, cadena), acepta_afd(minimo, cadena),
                             repr(cadena))


class PruebasFusionDeEquivalentes(unittest.TestCase):
    def test_dos_estados_equivalentes_se_fusionan(self):
        # S1 y S2 son ambos de aceptación y se comportan igual (todo va a sí
        # mismos): deben quedar en un solo estado.
        afd = AFD([0, 1, 2], ["a"], 0, {1, 2},
                  {(0, "a"): 1, (1, "a"): 1, (2, "a"): 2})
        minimo = minimizar(afd)
        self.assertEqual(len(minimo.estados), 2)

    def test_contiene_abb_se_reduce_a_cuatro(self):
        # subconjuntos da 5 (S0 y S2 equivalentes); minimización -> 4.
        antes = afd_de_expresion("(a|b)*abb")
        self.assertEqual(len(antes.estados), 5)
        self.assertEqual(len(minimizar(antes).estados), 4)

    def test_ejemplo_del_enunciado_se_reduce_a_cuatro(self):
        minimo = afd_minimo_de_expresion("(a|b)*abb(a|b)*")
        self.assertEqual(len(minimo.estados), 4)
        self.assertEqual(len(minimo.aceptacion), 1)


class PruebasCasosDegenerados(unittest.TestCase):
    def test_cerradura_es_un_solo_estado(self):
        for expresion in ("a*", "(a|b)*"):
            minimo = afd_minimo_de_expresion(expresion)
            self.assertEqual(len(minimo.estados), 1, expresion)
            self.assertTrue(minimo.es_aceptacion(minimo.inicial), expresion)

    def test_inicial_de_aceptacion_se_conserva(self):
        minimo = afd_minimo_de_expresion("a?")
        self.assertTrue(minimo.es_aceptacion(minimo.inicial))

    def test_sin_estados_de_aceptacion_no_rompe(self):
        afd = AFD([0, 1], ["a"], 0, set(), {(0, "a"): 1, (1, "a"): 0})
        minimo = minimizar(afd)
        self.assertEqual(len(minimo.aceptacion), 0)
        self.assertEqual(len(minimo.estados), 1)   # 0 y 1 son equivalentes

    def test_un_solo_estado_de_entrada_se_mantiene(self):
        afd = AFD([0], ["a"], 0, {0}, {(0, "a"): 0})
        minimo = minimizar(afd)
        self.assertEqual(len(minimo.estados), 1)
        self.assertTrue(minimo.es_aceptacion(0))

    def test_idempotencia(self):
        for expresion in ("a", "a*", "(a|b)*abb", "a+b?", "(b|b)*abb(a|b)*"):
            una = afd_minimo_de_expresion(expresion)
            dos = minimizar(una)
            self.assertEqual(len(una.estados), len(dos.estados), expresion)


class PruebasEquivalenciaDeLenguajes(unittest.TestCase):
    EXPRESIONES = ["a", "a|b", "ab", "a*", "(a|b)*", "(a|b)*abb",
                   "(a|b)*abb(a|b)*", "(b|b)*abb(a|b)*", "a+b?",
                   "((ε|a)|b*)*", "abb"]

    def test_afn_afd_y_minimo_coinciden(self):
        for expresion in self.EXPRESIONES:
            afn = afn_de_expresion(expresion)
            afd = afd_de_expresion(expresion)
            minimo = minimizar(afd)
            for cadena in cadenas_hasta(5):
                r_afn = acepta_afn(afn, cadena)
                r_afd = acepta_afd(afd, cadena)
                r_min = acepta_afd(minimo, cadena)
                self.assertEqual((r_afn, r_afn), (r_afd, r_min),
                                 "%r con %r -> afn=%s afd=%s min=%s"
                                 % (expresion, cadena, r_afn, r_afd, r_min))

    def test_abb_minimo_completo(self):
        # abb: AFD mínimo *completo* = 5 estados (4 + pozo).
        minimo = afd_minimo_de_expresion("abb")
        self.assertEqual(len(minimo.estados), 5)
        self.assertTrue(minimo.es_completo())


if __name__ == "__main__":
    unittest.main()
