"""pruebas del incremento 3: shunting yard (validación, concatenación, postfix)."""

import unittest

import contexto  # noqa: F401

from errores import ErrorExpresionVacia, ErrorOperador, ErrorParentesis
from shunting_yard import (CONCAT, a_postfix, convertir, infix_a_postfix,
                           insertar_concatenacion, postfix_a_texto, validar)
from tokenizador import SIMBOLO, tokenizar


def pf(expresion):
    """texto de la expresión en postfija (con '·' explícito)."""
    return postfix_a_texto(infix_a_postfix(expresion))


class PruebasCasosBasicos(unittest.TestCase):
    def test_un_simbolo(self):
        self.assertEqual(pf("a"), "a")

    def test_union(self):
        self.assertEqual(pf("a|b"), "ab|")

    def test_concatenacion(self):
        self.assertEqual(pf("ab"), "ab·")

    def test_cerradura(self):
        self.assertEqual(pf("a*"), "a*")

    def test_mas_y_opcional(self):
        self.assertEqual(pf("a+"), "a+")
        self.assertEqual(pf("a?"), "a?")

    def test_agrupacion(self):
        self.assertEqual(pf("(a|b)*"), "ab|*")

    def test_epsilon_se_concatena_como_cualquier_simbolo(self):
        self.assertEqual(pf("εa"), "εa·")


class PruebasPrecedenciaYAsociatividad(unittest.TestCase):
    def test_cerradura_antes_que_concatenacion(self):
        self.assertEqual(pf("ab*"), "ab*·")

    def test_concatenacion_antes_que_union(self):
        self.assertEqual(pf("ab|c"), "ab·c|")
        self.assertEqual(pf("a|bc"), "abc·|")

    def test_union_asociativa_por_la_izquierda(self):
        self.assertEqual(pf("a|b|c"), "ab|c|")

    def test_concatenacion_asociativa_por_la_izquierda(self):
        self.assertEqual(pf("abc"), "ab·c·")

    def test_unarios_encadenados(self):
        self.assertEqual(pf("a**"), "a**")
        self.assertEqual(pf("a+?"), "a+?")

    def test_ejemplo_del_enunciado(self):
        self.assertEqual(pf("(a|b)*abb(a|b)*"), "ab|*a·b·b·ab|*·")

    def test_ejemplo_del_enunciado_variante(self):
        self.assertEqual(pf("(b|b)*abb(a|b)*"), "bb|*a·b·b·ab|*·")


class PruebasInsercionDeConcatenacion(unittest.TestCase):
    def _tipos(self, expresion):
        return [t.tipo for t in insertar_concatenacion(tokenizar(expresion))]

    def test_se_inserta_entre_simbolos_pegados(self):
        self.assertEqual(self._tipos("ab").count(CONCAT), 1)

    def test_se_inserta_entre_grupo_y_simbolo(self):
        # (a|b)c  ->  un solo CONCAT, entre ')' y 'c'
        self.assertEqual(self._tipos("(a|b)c").count(CONCAT), 1)

    def test_se_inserta_despues_de_un_unario(self):
        # a*b  ->  CONCAT entre '*' y 'b'
        self.assertEqual(self._tipos("a*b").count(CONCAT), 1)

    def test_no_se_inserta_junto_a_la_union(self):
        self.assertEqual(self._tipos("a|b").count(CONCAT), 0)

    def test_no_se_inserta_dentro_de_parentesis_de_apertura(self):
        # "(a" no lleva CONCAT; "a)" tampoco
        self.assertEqual(self._tipos("(a)").count(CONCAT), 0)

    def test_la_posicion_del_concat_es_la_del_token_izquierdo(self):
        tokens = insertar_concatenacion(tokenizar("ab"))
        concat = next(t for t in tokens if t.tipo == CONCAT)
        self.assertEqual(concat.posicion, 0)


class PruebasSalidaSonTokens(unittest.TestCase):
    def test_a_postfix_devuelve_tokens(self):
        salida = convertir(tokenizar("a|b"))
        self.assertTrue(all(hasattr(t, "tipo") for t in salida))
        self.assertEqual([t.tipo for t in salida], [SIMBOLO, SIMBOLO, "UNION"])

    def test_conserva_la_posicion_de_los_simbolos(self):
        salida = convertir(tokenizar("ab|c"))
        simbolos = [t for t in salida if t.tipo == SIMBOLO]
        self.assertEqual([t.posicion for t in simbolos], [0, 1, 3])


class PruebasExpresionesMalFormadas(unittest.TestCase):
    def test_expresion_vacia(self):
        with self.assertRaises(ErrorExpresionVacia):
            convertir(tokenizar(""))

    def test_cerradura_sin_operando(self):
        with self.assertRaises(ErrorOperador):
            infix_a_postfix("*a")

    def test_mas_sin_operando_al_inicio(self):
        with self.assertRaises(ErrorOperador):
            infix_a_postfix("+a")

    def test_union_sin_operando_izquierdo(self):
        with self.assertRaises(ErrorOperador):
            infix_a_postfix("|a")

    def test_union_sin_operando_derecho(self):
        with self.assertRaises(ErrorOperador):
            infix_a_postfix("a|")

    def test_union_doble(self):
        with self.assertRaises(ErrorOperador):
            infix_a_postfix("a||b")

    def test_unario_despues_de_union(self):
        with self.assertRaises(ErrorOperador):
            infix_a_postfix("a|*b")

    def test_parentesis_sin_cerrar(self):
        with self.assertRaises(ErrorParentesis):
            infix_a_postfix("(a|b")

    def test_parentesis_de_sobra(self):
        with self.assertRaises(ErrorParentesis):
            infix_a_postfix("a|b)")

    def test_grupo_vacio(self):
        with self.assertRaises(ErrorParentesis):
            infix_a_postfix("()")

    def test_union_incompleta_dentro_de_parentesis(self):
        with self.assertRaises(ErrorOperador):
            infix_a_postfix("(a|)")

    def test_validar_devuelve_los_mismos_tokens_si_todo_esta_bien(self):
        tokens = tokenizar("(a|b)*abb")
        self.assertIs(validar(tokens), tokens)


if __name__ == "__main__":
    unittest.main()
