"""pruebas del incremento 2: tokenizador."""

import unittest

import contexto  # noqa: F401

from errores import ErrorSimbolo
from simbolos import EPSILON
from tokenizador import (ESTRELLA, LPAREN, MAS, OPCIONAL, RPAREN, SIMBOLO,
                         UNION, mostrar_valor, tokenizar)


def tipos(expresion):
    return [token.tipo for token in tokenizar(expresion)]


def valores(expresion):
    return [token.valor for token in tokenizar(expresion)]


class PruebasBasicas(unittest.TestCase):
    def test_un_simbolo(self):
        tokens = tokenizar("a")
        self.assertEqual(tokens, [(SIMBOLO, "a", 0)])

    def test_expresion_vacia_da_lista_vacia(self):
        self.assertEqual(tokenizar(""), [])

    def test_union(self):
        self.assertEqual(tipos("a|b"), [SIMBOLO, UNION, SIMBOLO])
        self.assertEqual(valores("a|b"), ["a", "|", "b"])

    def test_agrupacion_y_cerradura(self):
        self.assertEqual(tipos("(a|b)*"),
                         [LPAREN, SIMBOLO, UNION, SIMBOLO, RPAREN, ESTRELLA])

    def test_mas_y_opcional(self):
        self.assertEqual(tipos("a+b?"), [SIMBOLO, MAS, SIMBOLO, OPCIONAL])

    def test_posiciones(self):
        tokens = tokenizar("ab|c")
        self.assertEqual([t.posicion for t in tokens], [0, 1, 2, 3])


class PruebasEpsilon(unittest.TestCase):
    def test_epsilon_sin_escapar_es_el_objeto_epsilon(self):
        tokens = tokenizar("ε")
        self.assertEqual(tokens[0].tipo, SIMBOLO)
        self.assertIs(tokens[0].valor, EPSILON)

    def test_epsilon_en_medio_de_la_expresion(self):
        tokens = tokenizar("aεb")
        self.assertIs(tokens[1].valor, EPSILON)
        self.assertEqual(tokens[0].valor, "a")
        self.assertEqual(tokens[2].valor, "b")

    def test_epsilon_escapada_es_la_letra_griega_literal(self):
        tokens = tokenizar(r"\ε")
        self.assertEqual(tokens[0].tipo, SIMBOLO)
        self.assertEqual(tokens[0].valor, "ε")
        self.assertIsNot(tokens[0].valor, EPSILON)


class PruebasEscapes(unittest.TestCase):
    def test_metacaracteres_escapados_son_simbolos(self):
        for texto, esperado in ((r"\*", "*"), (r"\|", "|"), (r"\(", "("),
                                (r"\)", ")"), (r"\+", "+"), (r"\?", "?"),
                                (r"\\", "\\")):
            tokens = tokenizar(texto)
            self.assertEqual(tokens, [(SIMBOLO, esperado, 0)], texto)

    def test_escape_de_un_caracter_normal_es_ese_caracter(self):
        self.assertEqual(tokenizar(r"\a"), [(SIMBOLO, "a", 0)])

    def test_barra_cero_es_el_caracter_nulo(self):
        tokens = tokenizar(r"\0")
        self.assertEqual(tokens[0].valor, "\x00")
        self.assertEqual(len(tokens[0].valor), 1)

    def test_la_posicion_de_un_token_escapado_apunta_a_la_barra(self):
        tokens = tokenizar(r"a\*b")
        self.assertEqual([t.posicion for t in tokens], [0, 1, 3])

    def test_barra_al_final_es_error(self):
        with self.assertRaises(ErrorSimbolo):
            tokenizar("ab\\")
        with self.assertRaises(ErrorSimbolo):
            tokenizar("\\")


class PruebasCualquierCaracterEsSimbolo(unittest.TestCase):
    def test_el_espacio_es_un_simbolo(self):
        tokens = tokenizar("a b")
        self.assertEqual([t.valor for t in tokens], ["a", " ", "b"])

    def test_el_caracter_nulo_literal_es_un_simbolo(self):
        tokens = tokenizar("a\x00b")
        self.assertEqual([t.valor for t in tokens], ["a", "\x00", "b"])

    def test_el_punto_y_los_digitos_son_simbolos(self):
        self.assertEqual(tipos("0.1"), [SIMBOLO, SIMBOLO, SIMBOLO])

    def test_unicode_es_simbolo(self):
        tokens = tokenizar("λμ")
        self.assertEqual([t.valor for t in tokens], ["λ", "μ"])


class PruebasMostrarValor(unittest.TestCase):
    def test_epsilon(self):
        self.assertEqual(mostrar_valor(EPSILON), "ε")

    def test_nulo(self):
        self.assertEqual(mostrar_valor("\x00"), r"\0")

    def test_normal(self):
        self.assertEqual(mostrar_valor("a"), "a")


if __name__ == "__main__":
    unittest.main()
