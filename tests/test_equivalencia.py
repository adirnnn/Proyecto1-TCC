"""pruebas del incremento 11: equivalencia de lenguajes y casos borde.

lo más importante del proyecto: para cada expresión y cada cadena de un banco,
el **AFN**, el **AFD** por subconjuntos y el **AFD minimizado** deben dar
exactamente el mismo veredicto.  además, para las expresiones que se traducen
limpio a una expresión regular de python, se compara contra ``re.fullmatch``
como oráculo independiente.
"""

import itertools
import os
import re
import tempfile
import unittest

import contexto  # noqa: F401

from minimizacion import minimizar
from procesador import procesar_archivo
from simulador import acepta_afd, acepta_afn
from subconjuntos import afd_de_expresion
from thompson import afn_de_expresion


def cadenas_hasta(longitud, alfabeto):
    for n in range(longitud + 1):
        for tupla in itertools.product(alfabeto, repeat=n):
            yield "".join(tupla)


class PruebasEquivalenciaTresAutomatas(unittest.TestCase):
    BANCO = [
        ("a", "ab", 6),
        ("a|b", "ab", 6),
        ("ab", "ab", 6),
        ("a*", "ab", 6),
        ("a+", "ab", 6),
        ("a?", "ab", 6),
        ("(a|b)*", "ab", 6),
        ("(a|b)*abb", "ab", 7),
        ("(a|b)*abb(a|b)*", "ab", 7),
        ("(b|b)*abb(a|b)*", "ab", 7),
        ("a*b*", "ab", 6),
        ("(ab)*", "ab", 6),
        ("(a|b)(a|b)(a|b)", "ab", 5),
        ("a?b?c?", "abc", 4),
        ("(a|b|c)*", "abc", 4),
        ("((ε|a)|b*)*", "ab", 6),
        ("(a*)*", "ab", 6),
        ("(a*|b*)+", "ab", 6),
        ("abb", "ab", 6),
        ("λ|μ", "λμ", 5),
        ("(λμ)*", "λμ", 5),
    ]

    def test_afn_afd_minimo_coinciden(self):
        for expresion, alfabeto, longitud in self.BANCO:
            afn = afn_de_expresion(expresion)
            afd = afd_de_expresion(expresion)
            minimo = minimizar(afd)
            for cadena in cadenas_hasta(longitud, alfabeto):
                r_afn = acepta_afn(afn, cadena)
                r_afd = acepta_afd(afd, cadena)
                r_min = acepta_afd(minimo, cadena)
                self.assertTrue(r_afn == r_afd == r_min,
                                "%r con %r -> afn=%s afd=%s min=%s"
                                % (expresion, cadena, r_afn, r_afd, r_min))


class PruebasContraOraculoPython(unittest.TestCase):
    # expresiones cuya sintaxis coincide con la de re de python (ε -> grupo vacío)
    ORACULO = [
        ("a", "ab", 6), ("a|b", "ab", 6), ("ab", "ab", 6), ("a*", "ab", 6),
        ("a+", "ab", 6), ("a?", "ab", 6), ("(a|b)*", "ab", 6),
        ("(a|b)*abb", "ab", 7), ("(a|b)*abb(a|b)*", "ab", 6),
        ("a*b*", "ab", 6), ("(ab)*", "ab", 6), ("a?b?c?", "abc", 4),
        ("(a|b|c)*", "abc", 4), ("((ε|a)|b*)*", "ab", 6), ("(a*)*", "ab", 6),
        ("(a*|b*)+", "ab", 6), ("abb", "ab", 6),
    ]

    def test_afn_coincide_con_re_fullmatch(self):
        for expresion, alfabeto, longitud in self.ORACULO:
            patron = re.compile(expresion.replace("ε", "(?:)"))
            afn = afn_de_expresion(expresion)
            for cadena in cadenas_hasta(longitud, alfabeto):
                esperado = patron.fullmatch(cadena) is not None
                self.assertEqual(acepta_afn(afn, cadena), esperado,
                                 "%r con %r" % (expresion, cadena))


class PruebasCiclosEpsilon(unittest.TestCase):
    def test_terminan_y_son_consistentes(self):
        # todas tienen ciclos de ε (cerradura de algo anulable)
        for expresion in ("(a*)*", "(ε*)*", "((ε|a)|b*)*", "(a?|b?)*"):
            afn = afn_de_expresion(expresion)
            afd = afd_de_expresion(expresion)
            minimo = minimizar(afd)
            for cadena in cadenas_hasta(5, "ab"):
                self.assertTrue(
                    acepta_afn(afn, cadena) == acepta_afd(afd, cadena)
                    == acepta_afd(minimo, cadena), "%r %r" % (expresion, cadena))

    def test_expresiones_anulables_aceptan_la_cadena_vacia(self):
        for expresion in ("a*", "a?", "(a|b)*", "(a*)*", "ε", "a*b*"):
            self.assertTrue(acepta_afn(afn_de_expresion(expresion), ""), expresion)


class PruebasSimbolosInusuales(unittest.TestCase):
    def _tres_coinciden(self, expresion, cadena):
        afn = afn_de_expresion(expresion)
        afd = afd_de_expresion(expresion)
        minimo = minimizar(afd)
        r = acepta_afn(afn, cadena)
        self.assertEqual(r, acepta_afd(afd, cadena))
        self.assertEqual(r, acepta_afd(minimo, cadena))
        return r

    def test_caracter_nulo(self):
        self.assertTrue(self._tres_coinciden(r"a\0b", "a\x00b"))
        self.assertFalse(self._tres_coinciden(r"a\0b", "ab"))
        self.assertTrue(self._tres_coinciden(r"\0*", "\x00\x00\x00"))
        self.assertTrue(self._tres_coinciden(r"\0*", ""))

    def test_espacio_como_simbolo(self):
        self.assertTrue(self._tres_coinciden("a b", "a b"))
        self.assertFalse(self._tres_coinciden("a b", "ab"))
        self.assertTrue(self._tres_coinciden(" *", "   "))
        self.assertTrue(self._tres_coinciden("(a| )*", "a a "))

    def test_unicode(self):
        self.assertTrue(self._tres_coinciden("λμ", "λμ"))
        self.assertFalse(self._tres_coinciden("λμ", "λ"))
        self.assertTrue(self._tres_coinciden("(λ|μ)+", "μλλμ"))

    def test_metacaracteres_escapados_como_simbolos(self):
        self.assertTrue(self._tres_coinciden(r"\(\)", "()"))
        self.assertTrue(self._tres_coinciden(r"a\*b", "a*b"))
        self.assertTrue(self._tres_coinciden(r"\|*", "|||"))


class PruebasRechazoTrasCoincidenciaParcial(unittest.TestCase):
    def test_abc(self):
        afn = afn_de_expresion("abc")
        for cadena in ("ab", "abx", "abcd", "abca"):
            self.assertFalse(acepta_afn(afn, cadena), cadena)
        self.assertTrue(acepta_afn(afn, "abc"))

    def test_contiene_abb_al_final(self):
        afn = afn_de_expresion("(a|b)*abb")
        self.assertTrue(acepta_afn(afn, "aabb"))
        self.assertFalse(acepta_afn(afn, "abba"))


class PruebasDeadStateYMinimoCompleto(unittest.TestCase):
    def test_abb_minimo_tiene_pozo_y_es_consistente(self):
        afd = afd_de_expresion("abb")
        minimo = minimizar(afd)
        self.assertIsNotNone(minimo.estado_pozo)
        for cadena in cadenas_hasta(5, "ab"):
            self.assertEqual(acepta_afd(afd, cadena), acepta_afd(minimo, cadena),
                             cadena)


class PruebasExpresionGrande(unittest.TestCase):
    def test_no_rompe_y_es_consistente(self):
        expresion = "(a|b|c)*abc(a|b|c)*(a|b)*c?"
        afn = afn_de_expresion(expresion)
        afd = afd_de_expresion(expresion)
        minimo = minimizar(afd)
        self.assertLessEqual(len(minimo.estados), len(afd.estados))
        for cadena in cadenas_hasta(4, "abc"):
            self.assertTrue(
                acepta_afn(afn, cadena) == acepta_afd(afd, cadena)
                == acepta_afd(minimo, cadena), cadena)

    def test_anidamiento_profundo(self):
        afn = afn_de_expresion("((((a))))")
        self.assertTrue(acepta_afn(afn, "a"))
        self.assertFalse(acepta_afn(afn, "aa"))


class PruebasArchivoRobusto(unittest.TestCase):
    def test_crlf_sin_salto_final_duplicados_y_vacias(self):
        contenido = "a|b\r\n\r\n# comentario\r\na|b\r\n(a|b)*abb"  # sin \n final
        descriptor, ruta = tempfile.mkstemp(suffix=".txt")
        os.close(descriptor)
        with open(ruta, "w", encoding="utf-8", newline="") as archivo:
            archivo.write(contenido)
        self.addCleanup(os.remove, ruta)

        resultados = procesar_archivo(ruta, cadenas_globales=["ab"],
                                      generar_imagenes=False)
        # 3 expresiones: "a|b", "a|b" (duplicada), "(a|b)*abb"
        self.assertEqual(len(resultados), 3)
        self.assertFalse(any(r.hubo_error for r in resultados))
        self.assertEqual(resultados[0].expresion, resultados[1].expresion)

    def test_linea_solo_con_espacios_se_omite(self):
        descriptor, ruta = tempfile.mkstemp(suffix=".txt")
        os.close(descriptor)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("a\n   \n\t\nb\n")
        self.addCleanup(os.remove, ruta)
        resultados = procesar_archivo(ruta, cadenas_globales=[""],
                                      generar_imagenes=False)
        self.assertEqual([r.expresion for r in resultados], ["a", "b"])


class PruebasDeterminismo(unittest.TestCase):
    def test_misma_expresion_mismo_resultado(self):
        for expresion in ("(a|b)*abb(a|b)*", "((ε|a)|b*)*", "a?b+"):
            a1 = afd_de_expresion(expresion)
            a2 = afd_de_expresion(expresion)
            self.assertEqual(len(a1.estados), len(a2.estados))
            self.assertEqual(a1.transiciones, a2.transiciones)
            self.assertEqual(len(minimizar(a1).estados), len(minimizar(a2).estados))


if __name__ == "__main__":
    unittest.main()
