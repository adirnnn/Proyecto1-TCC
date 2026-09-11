"""pruebas de la extensión: clases de caracteres ``[...]`` y ``\\s``.

no las pide el enunciado, pero las necesitan expresiones reales como las que
usa el examen (identificadores, rangos de letras/dígitos, espacio en blanco).
se construyen exactamente igual que un símbolo normal: una clase ``[abc]`` es
"cualquiera de estos", como si fuera ``(a|b|c)`` pero sin gastar estados de
más por cada letra.
"""

import unittest

import contexto  # noqa: F401

from errores import ErrorSimbolo
from simulador import acepta_afd, acepta_afn
from subconjuntos import afd_de_expresion
from thompson import afn_de_expresion
from tokenizador import SIMBOLO, tokenizar


def afn_acepta(expresion, cadena):
    return acepta_afn(afn_de_expresion(expresion), cadena)


def afd_acepta(expresion, cadena):
    return acepta_afd(afd_de_expresion(expresion), cadena)


class PruebasTokenizacion(unittest.TestCase):
    def test_clase_produce_un_solo_token_simbolo(self):
        tokens = tokenizar("[abc]")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].tipo, SIMBOLO)
        self.assertEqual(tokens[0].valor, frozenset("abc"))

    def test_rango_se_expande(self):
        tokens = tokenizar("[a-e]")
        self.assertEqual(tokens[0].valor, frozenset("abcde"))

    def test_rangos_combinados_con_literales(self):
        tokens = tokenizar("[A-Za-z0-9_]")
        esperado = frozenset(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_")
        self.assertEqual(tokens[0].valor, esperado)

    def test_guion_al_inicio_o_al_final_es_literal(self):
        self.assertEqual(tokenizar("[-az]")[0].valor, frozenset({"-", "a", "z"}))
        self.assertEqual(tokenizar("[az-]")[0].valor, frozenset({"a", "z", "-"}))

    def test_guion_escapado_es_literal_aunque_este_en_medio(self):
        self.assertEqual(tokenizar(r"[a\-z]")[0].valor, frozenset({"a", "-", "z"}))

    def test_corchete_de_cierre_escapado_dentro_de_la_clase(self):
        self.assertEqual(tokenizar(r"[a\]b]")[0].valor, frozenset({"a", "]", "b"}))

    def test_barra_invertida_escapada_dentro_de_la_clase(self):
        self.assertEqual(tokenizar(r"[a\\b]")[0].valor, frozenset({"a", "\\", "b"}))

    def test_s_dentro_de_una_clase_agrega_espacio_y_tab(self):
        self.assertEqual(tokenizar(r"[a\sb]")[0].valor,
                         frozenset({"a", " ", "\t", "b"}))

    def test_clase_vacia_es_error(self):
        with self.assertRaises(ErrorSimbolo):
            tokenizar("[]")

    def test_clase_sin_cerrar_es_error(self):
        with self.assertRaises(ErrorSimbolo):
            tokenizar("[abc")

    def test_rango_invertido_es_error(self):
        with self.assertRaises(ErrorSimbolo):
            tokenizar("[z-a]")

    def test_barra_s_fuera_de_una_clase_es_espacio_y_tab(self):
        self.assertEqual(tokenizar(r"\s")[0].valor, frozenset({" ", "\t"}))


class PruebasSimulacion(unittest.TestCase):
    def test_clase_equivale_a_una_union(self):
        for cadena, esperado in (("a", True), ("b", True), ("c", True), ("d", False)):
            self.assertEqual(afn_acepta("[abc]", cadena), esperado, cadena)

    def test_rango_de_letras(self):
        self.assertTrue(afn_acepta("[a-z]+", "hola"))
        self.assertFalse(afn_acepta("[a-z]+", "Hola"))   # mayúscula fuera del rango

    def test_identificador_tipo_variable(self):
        # primera letra, luego letras/dígitos/guion bajo
        identificador = "[A-Za-z_][A-Za-z0-9_]*"
        for cadena in ("x", "nombre", "_temp", "var2", "CONST_1"):
            self.assertTrue(afn_acepta(identificador, cadena), cadena)
        for cadena in ("2var", "", "a-b"):
            self.assertFalse(afn_acepta(identificador, cadena), cadena)

    def test_espacio_en_blanco_con_barra_s(self):
        self.assertTrue(afn_acepta(r"a\sb", "a b"))
        self.assertTrue(afn_acepta(r"a\sb", "a\tb"))
        self.assertFalse(afn_acepta(r"a\sb", "ab"))
        self.assertFalse(afn_acepta(r"a\sb", "a\nb"))   # \n no es \s aquí

    def test_afn_y_afd_concuerdan_con_clases(self):
        for expresion, cadenas in (
                ("[a-c]*", ["", "a", "abc", "cba", "d"]),
                (r"[A-Z][a-z]*\s[0-9]+", ["Hola 123", "X 0", "hola 1", "Hi1 2"]),
        ):
            for cadena in cadenas:
                self.assertEqual(afn_acepta(expresion, cadena),
                                 afd_acepta(expresion, cadena),
                                 "%r con %r" % (expresion, cadena))


class PruebasExpresionDelExamen(unittest.TestCase):
    """la expresión de gramáticas (BNF) que dio el catedrático, con sus 3 cadenas."""

    EXPRESION = r"[A-Z][A-Za-z0-9_]*\s*::?=\s*([A-Za-z0-9_|'\"\s\[\](){}*+?\\-]|\|)+"

    def test_acepta_regla_simple(self):
        self.assertTrue(afn_acepta(self.EXPRESION, "S ::= A B | C"))
        self.assertTrue(afd_acepta(self.EXPRESION, "S ::= A B | C"))

    def test_acepta_regla_con_comillas_y_simbolos(self):
        cadena = "EXPR ::= term '+' term | term"
        self.assertTrue(afn_acepta(self.EXPRESION, cadena))
        self.assertTrue(afd_acepta(self.EXPRESION, cadena))

    def test_rechaza_si_no_empieza_con_mayuscula(self):
        cadena = "123VAR = value"
        self.assertFalse(afn_acepta(self.EXPRESION, cadena))
        self.assertFalse(afd_acepta(self.EXPRESION, cadena))


if __name__ == "__main__":
    unittest.main()
