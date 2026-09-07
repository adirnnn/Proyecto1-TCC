"""pruebas del incremento 6: cerradura ε, mover y construcción de subconjuntos."""

import unittest

import contexto  # noqa: F401

from automata import AFN, Estado
from simbolos import EPSILON
from subconjuntos import afd_de_expresion, afn_a_afd, cerradura_epsilon, mover
from thompson import afn_de_expresion


class PruebasCerraduraEpsilon(unittest.TestCase):
    def test_incluye_los_estados_de_partida(self):
        q0 = Estado(0)
        self.assertEqual(cerradura_epsilon({q0}), frozenset({q0}))

    def test_sigue_cadenas_de_epsilon(self):
        q0, q1, q2 = Estado(0), Estado(1), Estado(2)
        q0.agregar_transicion(EPSILON, q1)
        q1.agregar_transicion(EPSILON, q2)
        self.assertEqual(cerradura_epsilon({q0}), frozenset({q0, q1, q2}))

    def test_tolera_ciclos_de_epsilon(self):
        q0, q1 = Estado(0), Estado(1)
        q0.agregar_transicion(EPSILON, q1)
        q1.agregar_transicion(EPSILON, q0)      # ciclo
        self.assertEqual(cerradura_epsilon({q0}), frozenset({q0, q1}))

    def test_no_cruza_transiciones_con_simbolo(self):
        q0, q1 = Estado(0), Estado(1)
        q0.agregar_transicion("a", q1)
        self.assertEqual(cerradura_epsilon({q0}), frozenset({q0}))


class PruebasMover(unittest.TestCase):
    def test_mueve_por_el_simbolo_y_no_aplica_cerradura(self):
        q0, q1, q2 = Estado(0), Estado(1), Estado(2)
        q0.agregar_transicion("a", q1)
        q1.agregar_transicion(EPSILON, q2)
        self.assertEqual(mover({q0}, "a"), frozenset({q1}))   # q2 NO entra

    def test_ignora_epsilon(self):
        q0, q1 = Estado(0), Estado(1)
        q0.agregar_transicion(EPSILON, q1)
        self.assertEqual(mover({q0}, "a"), frozenset())

    def test_reune_destinos_de_varios_estados(self):
        q0, q1, q2 = Estado(0), Estado(1), Estado(2)
        q0.agregar_transicion("a", q1)
        q2.agregar_transicion("a", q1)
        self.assertEqual(mover({q0, q2}, "a"), frozenset({q1}))


class PruebasConstruccion(unittest.TestCase):
    def test_un_simbolo(self):
        afd = afd_de_expresion("a")
        self.assertEqual(len(afd.estados), 2)
        self.assertEqual(afd.transicion(0, "a"), 1)
        self.assertTrue(afd.es_aceptacion(1))
        self.assertFalse(afd.es_aceptacion(0))
        self.assertEqual(afd.alfabeto, ["a"])

    def test_es_determinista(self):
        afd = afd_de_expresion("(a|b)*abb")
        for clave, destino in afd.transiciones.items():
            self.assertIsInstance(destino, int)
        # a lo sumo un destino por (estado, símbolo): garantizado por ser dict
        self.assertEqual(len(afd.transiciones),
                         len(set(afd.transiciones.keys())))

    def test_no_crea_dos_veces_el_mismo_subconjunto(self):
        # 'a|a' -> las dos ramas leen 'a' y caen en el mismo subconjunto
        afd = afd_de_expresion("a|a")
        self.assertEqual(len(afd.estados), 2)

    def test_estado_inicial_de_aceptacion_cuando_se_acepta_epsilon(self):
        for expresion in ("a*", "a?", "(a|b)*"):
            afd = afd_de_expresion(expresion)
            self.assertTrue(afd.es_aceptacion(afd.inicial), expresion)

    def test_puede_quedar_parcial(self):
        # 'ab' sobre alfabeto {a,b}: desde el estado inicial no hay transición 'b'
        afd = afd_de_expresion("ab")
        self.assertFalse(afd.es_completo())

    def test_ejemplo_clasico_contiene_abb(self):
        # subconjuntos da 5 estados (S0 y S2 resultan equivalentes: la
        # minimización los fusiona y deja el AFD "de libro" de 4 estados).
        afd = afd_de_expresion("(a|b)*abb")
        self.assertEqual(len(afd.estados), 5)
        self.assertTrue(afd.es_completo())
        self.assertEqual(len(afd.aceptacion), 1)

    def test_descripciones_nombran_estados_del_afn(self):
        afd = afd_de_expresion("a")
        self.assertTrue(afd.descripcion(0).startswith("{q"))

    def test_alfabeto_se_toma_del_afn(self):
        afn = afn_de_expresion("a|b")
        afd = afn_a_afd(afn)
        self.assertEqual(afd.alfabeto, ["a", "b"])

    def test_afn_sin_simbolos_solo_epsilon(self):
        # 'ε' -> AFD de un solo estado, de aceptación, alfabeto vacío
        afd = afd_de_expresion("ε")
        self.assertEqual(len(afd.estados), 1)
        self.assertTrue(afd.es_aceptacion(0))
        self.assertEqual(afd.alfabeto, [])


if __name__ == "__main__":
    unittest.main()
