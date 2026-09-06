"""pruebas del incremento 1: constantes básicas y jerarquía de errores."""

import unittest

import contexto  # noqa: F401

from errores import ErrorArchivo, ErrorProyecto, ErrorRegex
from simbolos import (EPSILON, EPSILON_ENTRADA, ESCAPES, METACARACTERES,
                      _Epsilon)


class PruebasEpsilon(unittest.TestCase):
    def test_no_es_cadena(self):
        # importante: ninguna letra del alfabeto puede colisionar con epsilon.
        self.assertNotIsInstance(EPSILON, str)

    def test_no_es_none(self):
        # None se reserva para "aquí no hay transición".
        self.assertIsNotNone(EPSILON)

    def test_se_muestra_como_letra_griega(self):
        self.assertEqual(str(EPSILON), "ε")

    def test_es_singleton(self):
        self.assertIs(EPSILON, _Epsilon())

    def test_distinto_de_simbolos_riesgosos(self):
        for simbolo in ("\x00", " ", "ε", "e", EPSILON_ENTRADA, ""):
            self.assertNotEqual(EPSILON, simbolo)


class PruebasConstantes(unittest.TestCase):
    def test_los_siete_metacaracteres(self):
        self.assertEqual(METACARACTERES, frozenset("()|*+?\\"))
        self.assertEqual(len(METACARACTERES), 7)

    def test_escape_del_caracter_nulo(self):
        self.assertEqual(ESCAPES["0"], "\x00")
        self.assertEqual(len(ESCAPES["0"]), 1)


class PruebasJerarquiaDeErrores(unittest.TestCase):
    def test_errores_de_regex_heredan_del_error_base(self):
        self.assertTrue(issubclass(ErrorRegex, ErrorProyecto))

    def test_error_de_archivo_hereda_del_error_base(self):
        self.assertTrue(issubclass(ErrorArchivo, ErrorProyecto))


if __name__ == "__main__":
    unittest.main()
