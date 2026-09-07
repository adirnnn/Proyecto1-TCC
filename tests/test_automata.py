"""pruebas del incremento 4: estructuras ``AFN`` y ``AFD``."""

import unittest

import contexto  # noqa: F401

from automata import AFD, AFN, Estado, Transicion
from simbolos import EPSILON


def afn_de_un_simbolo(simbolo):
    """AFN mínimo (q0) --simbolo--> (q1), con q1 de aceptación."""
    q0, q1 = Estado(0), Estado(1)
    q0.agregar_transicion(simbolo, q1)
    return AFN([q0, q1], q0, q1)


class PruebasEstado(unittest.TestCase):
    def test_nombre(self):
        self.assertEqual(Estado(3).nombre, "q3")

    def test_agregar_transicion(self):
        q0, q1 = Estado(0), Estado(1)
        q0.agregar_transicion("a", q1)
        self.assertEqual(q0.transiciones, [("a", q1)])


class PruebasAFN(unittest.TestCase):
    def test_alfabeto_excluye_epsilon(self):
        q0, q1, q2 = Estado(0), Estado(1), Estado(2)
        q0.agregar_transicion(EPSILON, q1)
        q1.agregar_transicion("a", q2)
        afn = AFN([q0, q1, q2], q0, q2)
        self.assertEqual(afn.alfabeto, {"a"})

    def test_alfabeto_vacio_si_solo_hay_epsilon(self):
        q0, q1 = Estado(0), Estado(1)
        q0.agregar_transicion(EPSILON, q1)
        self.assertEqual(AFN([q0, q1], q0, q1).alfabeto, set())

    def test_es_aceptacion_compara_por_identidad(self):
        afn = afn_de_un_simbolo("a")
        self.assertTrue(afn.es_aceptacion(afn.aceptacion))
        self.assertFalse(afn.es_aceptacion(afn.inicial))

    def test_transiciones_devuelve_objetos_transicion(self):
        afn = afn_de_un_simbolo("a")
        transiciones = afn.transiciones()
        self.assertEqual(len(transiciones), 1)
        self.assertIsInstance(transiciones[0], Transicion)
        self.assertEqual(transiciones[0].simbolo, "a")
        self.assertFalse(transiciones[0].es_epsilon)

    def test_transicion_epsilon_se_reconoce(self):
        q0, q1 = Estado(0), Estado(1)
        q0.agregar_transicion(EPSILON, q1)
        afn = AFN([q0, q1], q0, q1)
        self.assertTrue(afn.transiciones()[0].es_epsilon)

    def test_resumen_menciona_estados_y_alfabeto(self):
        resumen = afn_de_un_simbolo("a").resumen()
        self.assertIn("2 estados", resumen)
        self.assertIn("{a}", resumen)


def afd_ejemplo():
    """AFD de 'las cadenas sobre {a,b} que terminan en a'. S1 es de aceptación."""
    transiciones = {
        (0, "a"): 1, (0, "b"): 0,
        (1, "a"): 1, (1, "b"): 0,
    }
    return AFD([0, 1], ["a", "b"], 0, {1}, transiciones)


class PruebasAFD(unittest.TestCase):
    def test_transicion_definida(self):
        self.assertEqual(afd_ejemplo().transicion(0, "a"), 1)

    def test_transicion_faltante_es_none(self):
        afd = AFD([0], ["a"], 0, set(), {})
        self.assertIsNone(afd.transicion(0, "a"))

    def test_es_aceptacion(self):
        afd = afd_ejemplo()
        self.assertTrue(afd.es_aceptacion(1))
        self.assertFalse(afd.es_aceptacion(0))

    def test_es_completo(self):
        self.assertTrue(afd_ejemplo().es_completo())
        parcial = AFD([0, 1], ["a", "b"], 0, {1}, {(0, "a"): 1})
        self.assertFalse(parcial.es_completo())

    def test_nombre_de_estado_normal_y_pozo(self):
        afd = AFD([0, 1], ["a"], 0, set(), {(0, "a"): 1, (1, "a"): 1}, estado_pozo=1)
        self.assertEqual(afd.nombre(0), "S0")
        self.assertEqual(afd.nombre(1), "P")

    def test_alfabeto_queda_ordenado(self):
        afd = AFD([0], ["b", "a"], 0, set(), {})
        self.assertEqual(afd.alfabeto, ["a", "b"])

    def test_tabla_marca_inicial_y_aceptacion(self):
        tabla = afd_ejemplo().tabla()
        self.assertIn("->S0", tabla)
        self.assertIn("*S1", tabla)
        self.assertIn("estado", tabla)

    def test_transiciones_ordenadas(self):
        ordenadas = afd_ejemplo().transiciones_ordenadas()
        self.assertEqual(ordenadas[0], (0, "a", 1))
        self.assertEqual(ordenadas, sorted(ordenadas, key=lambda t: (t[0], str(t[1]))))

    def test_descripcion_por_defecto_es_cadena_vacia(self):
        self.assertEqual(afd_ejemplo().descripcion(0), "")

    def test_resumen_menciona_aceptacion(self):
        self.assertIn("{S1}", afd_ejemplo().resumen())


if __name__ == "__main__":
    unittest.main()
