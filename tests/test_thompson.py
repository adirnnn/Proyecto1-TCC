"""pruebas del incremento 5: construcción de thompson (estructura del AFN)."""

import unittest

import contexto  # noqa: F401

from automata import AFN
from errores import ErrorRegex
from simbolos import EPSILON
from thompson import afn_de_expresion, construir_afn


def afn(expresion):
    return afn_de_expresion(expresion)


def n_transiciones(automata):
    return sum(len(e.transiciones) for e in automata.estados)


def n_epsilon(automata):
    return sum(1 for t in automata.transiciones() if t.es_epsilon)


class PruebasEstructura(unittest.TestCase):
    def test_un_simbolo(self):
        a = afn("a")
        self.assertEqual(len(a.estados), 2)
        self.assertEqual(n_transiciones(a), 1)
        self.assertEqual(n_epsilon(a), 0)
        self.assertEqual(a.alfabeto, {"a"})

    def test_epsilon_como_hoja(self):
        a = afn("ε")
        self.assertEqual(len(a.estados), 2)
        self.assertEqual(a.alfabeto, set())
        self.assertTrue(a.transiciones()[0].es_epsilon)

    def test_concatenacion_no_agrega_estados_y_agrega_una_epsilon(self):
        a = afn("ab")
        self.assertEqual(len(a.estados), 4)        # 2 + 2
        self.assertEqual(n_epsilon(a), 1)          # el puente entre fragmentos

    def test_union_agrega_dos_estados_y_cuatro_epsilon(self):
        a = afn("a|b")
        self.assertEqual(len(a.estados), 6)        # 2 + 2 + 2
        self.assertEqual(n_epsilon(a), 4)

    def test_cerradura_agrega_dos_estados_y_cuatro_epsilon(self):
        a = afn("a*")
        self.assertEqual(len(a.estados), 4)        # 2 + 2
        self.assertEqual(n_epsilon(a), 4)

    def test_una_o_mas_agrega_dos_estados_y_tres_epsilon(self):
        a = afn("a+")
        self.assertEqual(len(a.estados), 4)
        self.assertEqual(n_epsilon(a), 3)

    def test_opcional_agrega_dos_estados_y_tres_epsilon(self):
        a = afn("a?")
        self.assertEqual(len(a.estados), 4)
        self.assertEqual(n_epsilon(a), 3)

    def test_ejemplo_del_enunciado_tamano(self):
        # (a|b)*abb(a|b)*  : 7 hojas -> 14, mas 2 uniones y 2 cerraduras -> +8
        a = afn("(a|b)*abb(a|b)*")
        self.assertEqual(len(a.estados), 22)
        self.assertEqual(a.alfabeto, {"a", "b"})


class PruebasInvariantes(unittest.TestCase):
    def _tiene_entrantes(self, automata, objetivo):
        return any(destino is objetivo
                   for e in automata.estados for _, destino in e.transiciones)

    def test_un_unico_estado_de_aceptacion_sin_salidas(self):
        for expresion in ("a", "a*", "a|b", "(a|b)*abb", "a+b?", "ε"):
            a = afn(expresion)
            self.assertEqual(a.aceptacion.transiciones, [], expresion)

    def test_el_inicial_no_tiene_transiciones_entrantes(self):
        for expresion in ("a", "a*", "a|b", "(a|b)*abb", "a+", "a?"):
            a = afn(expresion)
            self.assertFalse(self._tiene_entrantes(a, a.inicial), expresion)

    def test_numeracion_bfs_desde_cero(self):
        a = afn("(a|b)*abb")
        self.assertEqual([e.numero for e in a.estados],
                         list(range(len(a.estados))))
        self.assertEqual(a.inicial.numero, 0)

    def test_devuelve_un_afn(self):
        self.assertIsInstance(afn("a"), AFN)


class PruebasErrores(unittest.TestCase):
    def test_postfija_vacia(self):
        with self.assertRaises(ErrorRegex):
            construir_afn([])


if __name__ == "__main__":
    unittest.main()
