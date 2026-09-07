"""pruebas del incremento 7: simulación de la cadena w en el AFN y en el AFD."""

import unittest

import contexto  # noqa: F401

from simulador import (NO, SI, acepta_afd, acepta_afn, respuesta, simular_afd,
                       simular_afn)
from subconjuntos import afd_de_expresion
from thompson import afn_de_expresion


def afn_acepta(expresion, cadena):
    return acepta_afn(afn_de_expresion(expresion), cadena)


def afd_acepta(expresion, cadena):
    return acepta_afd(afd_de_expresion(expresion), cadena)


class PruebasAFN(unittest.TestCase):
    def test_literal(self):
        self.assertTrue(afn_acepta("a", "a"))
        self.assertFalse(afn_acepta("a", ""))
        self.assertFalse(afn_acepta("a", "b"))
        self.assertFalse(afn_acepta("a", "aa"))

    def test_epsilon_acepta_la_cadena_vacia(self):
        self.assertTrue(afn_acepta("ε", ""))
        self.assertFalse(afn_acepta("ε", "a"))

    def test_concatenacion(self):
        self.assertTrue(afn_acepta("abb", "abb"))
        self.assertFalse(afn_acepta("abb", "ab"))
        self.assertFalse(afn_acepta("abb", "abbb"))

    def test_union(self):
        self.assertTrue(afn_acepta("a|b", "a"))
        self.assertTrue(afn_acepta("a|b", "b"))
        self.assertFalse(afn_acepta("a|b", "c"))
        self.assertFalse(afn_acepta("a|b", ""))

    def test_cerradura(self):
        self.assertTrue(afn_acepta("a*", ""))
        self.assertTrue(afn_acepta("a*", "aaaa"))
        self.assertFalse(afn_acepta("a*", "b"))

    def test_una_o_mas(self):
        self.assertFalse(afn_acepta("a+", ""))
        self.assertTrue(afn_acepta("a+", "a"))
        self.assertTrue(afn_acepta("a+", "aaa"))

    def test_opcional(self):
        self.assertTrue(afn_acepta("a?", ""))
        self.assertTrue(afn_acepta("a?", "a"))
        self.assertFalse(afn_acepta("a?", "aa"))

    def test_rechazo_tras_coincidencia_parcial(self):
        self.assertTrue(afn_acepta("(a|b)*abb", "abb"))
        self.assertFalse(afn_acepta("(a|b)*abb", "abba"))

    def test_ejemplo_del_enunciado(self):
        self.assertTrue(afn_acepta("(b|b)*abb(a|b)*", "babbaaaa"))
        self.assertFalse(afn_acepta("(b|b)*abb(a|b)*", "ba"))


class PruebasAFD(unittest.TestCase):
    def test_casos_basicos(self):
        self.assertTrue(afd_acepta("(a|b)*abb", "aabb"))
        self.assertTrue(afd_acepta("(a|b)*abb", "babb"))
        self.assertFalse(afd_acepta("(a|b)*abb", "ab"))
        self.assertFalse(afd_acepta("(a|b)*abb", ""))

    def test_simbolo_fuera_del_alfabeto(self):
        acepta, pasos = simular_afd(afd_de_expresion("a"), "x")
        self.assertFalse(acepta)
        self.assertIn("alfabeto", pasos[-1])

    def test_sin_transicion_definida(self):
        acepta, pasos = simular_afd(afd_de_expresion("ab"), "b")
        self.assertFalse(acepta)
        self.assertIn("transición", pasos[-1])

    def test_ejemplo_del_enunciado(self):
        self.assertTrue(afd_acepta("(b|b)*abb(a|b)*", "babbaaaa"))
        self.assertFalse(afd_acepta("(b|b)*abb(a|b)*", "ba"))


class PruebasSimbolosInusuales(unittest.TestCase):
    def test_caracter_nulo_como_simbolo(self):
        self.assertTrue(afn_acepta(r"a\0b", "a\x00b"))
        self.assertTrue(afd_acepta(r"a\0b", "a\x00b"))
        self.assertFalse(afd_acepta(r"a\0b", "ab"))

    def test_espacio_como_dato(self):
        self.assertTrue(afn_acepta("a b", "a b"))
        self.assertFalse(afn_acepta("a b", "ab"))


class PruebasAFNyAFDConcuerdan(unittest.TestCase):
    BANCO = [
        ("a", ["", "a", "b", "aa"]),
        ("a|b", ["", "a", "b", "ab", "c"]),
        ("ab", ["ab", "a", "abb", ""]),
        ("a*", ["", "a", "aaaa", "b"]),
        ("(a|b)*", ["", "a", "abba", "abc"]),
        ("(a|b)*abb", ["abb", "aabb", "babb", "ab", "abba", ""]),
        ("(b|b)*abb(a|b)*", ["babbaaaa", "abb", "ba", "aaa", ""]),
        ("a+b?", ["a", "ab", "aab", "", "b"]),
        ("((ε|a)|b*)*", ["", "aab", "bbb", "c"]),
    ]

    def test_mismo_veredicto(self):
        for expresion, cadenas in self.BANCO:
            afn = afn_de_expresion(expresion)
            afd = afd_de_expresion(expresion)
            for cadena in cadenas:
                self.assertEqual(acepta_afn(afn, cadena), acepta_afd(afd, cadena),
                                 "%r con %r" % (expresion, cadena))


class PruebasTrazaYRespuesta(unittest.TestCase):
    def test_respuesta_es_si_o_no(self):
        self.assertEqual(respuesta(True), SI)
        self.assertEqual(respuesta(False), NO)
        self.assertEqual((SI, NO), ("sí", "no"))

    def test_la_traza_del_afn_empieza_por_la_cerradura(self):
        _, pasos = simular_afn(afn_de_expresion("a"), "a")
        self.assertIn("cerradura", pasos[0])

    def test_la_traza_del_afd_lista_un_paso_por_simbolo_leido(self):
        _, pasos = simular_afd(afd_de_expresion("(a|b)*abb"), "abb")
        # 1 línea del estado inicial + 3 símbolos
        self.assertEqual(len(pasos), 4)


if __name__ == "__main__":
    unittest.main()
