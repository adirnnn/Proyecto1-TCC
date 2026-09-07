"""pruebas del incremento 10: integración (archivo -> pipeline -> salida).

la equivalencia exhaustiva AFN = AFD = AFD mínimo sobre bancos de cadenas se
amplía en el incremento 11; aquí se prueba el flujo del programa: leer el
archivo, procesar cada línea, tolerar errores y devolver el código de salida.
"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import contexto  # noqa: F401

import main
from procesador import (ResultadoSimulacion, procesar_archivo, procesar_expresion,
                        separar_expresion_y_cadenas)


def archivo_temporal(contenido):
    descriptor, ruta = tempfile.mkstemp(suffix=".txt")
    os.close(descriptor)
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        archivo.write(contenido)
    return ruta


class PruebasSepararLinea(unittest.TestCase):
    def test_sin_punto_y_coma(self):
        self.assertEqual(separar_expresion_y_cadenas("(a|b)*"), ("(a|b)*", []))

    def test_con_cadenas(self):
        self.assertEqual(separar_expresion_y_cadenas("ab;a,ab,abc"),
                         ("ab", ["a", "ab", "abc"]))

    def test_cadena_vacia_al_final(self):
        self.assertEqual(separar_expresion_y_cadenas("a*;aa,"), ("a*", ["aa", ""]))

    def test_solo_punto_y_coma_no_da_cadenas(self):
        self.assertEqual(separar_expresion_y_cadenas("a*;"), ("a*", []))


class PruebasProcesarArchivo(unittest.TestCase):
    def test_una_linea_con_error_no_detiene_las_demas(self):
        ruta = archivo_temporal("(a|b\n*a\na|\n(a|b)*abb\n")
        self.addCleanup(os.remove, ruta)
        resultados = procesar_archivo(ruta, generar_imagenes=False)
        self.assertEqual(len(resultados), 4)
        self.assertTrue(resultados[0].hubo_error)   # (a|b
        self.assertTrue(resultados[1].hubo_error)   # *a
        self.assertTrue(resultados[2].hubo_error)   # a|
        self.assertFalse(resultados[3].hubo_error)  # (a|b)*abb

    def test_cadenas_por_linea_tienen_prioridad_sobre_las_globales(self):
        ruta = archivo_temporal("a*;aaa\n")
        self.addCleanup(os.remove, ruta)
        resultados = procesar_archivo(ruta, cadenas_globales=["zzz"],
                                      generar_imagenes=False)
        self.assertEqual(len(resultados[0].simulaciones), 1)
        self.assertEqual(resultados[0].simulaciones[0].cadena, "aaa")

    def test_genera_las_tres_imagenes_por_expresion(self):
        ruta = archivo_temporal("(a|b)*abb\n")
        self.addCleanup(os.remove, ruta)
        with tempfile.TemporaryDirectory() as carpeta:
            resultados = procesar_archivo(ruta, carpeta_salida=carpeta,
                                          generar_imagenes=True)
            imagenes = resultados[0].imagenes
            self.assertEqual(set(imagenes), {"afn", "afd", "afd_minimo"})
            for ruta_svg, ruta_dot in imagenes.values():
                self.assertTrue(os.path.exists(ruta_svg))
                self.assertTrue(os.path.exists(ruta_dot))


class PruebasEjemploDelEnunciado(unittest.TestCase):
    def test_babbaaaa_pertenece(self):
        resultado = procesar_expresion(1, "(b|b)*abb(a|b)*", ["babbaaaa"],
                                       generar_imagenes=False)
        self.assertFalse(resultado.hubo_error)
        simulacion = resultado.simulaciones[0]
        self.assertTrue(simulacion.acepta)
        self.assertEqual(simulacion.respuesta, "sí")
        self.assertTrue(simulacion.coinciden)

    def test_ba_no_pertenece(self):
        resultado = procesar_expresion(1, "(b|b)*abb(a|b)*", ["ba"],
                                       generar_imagenes=False)
        self.assertFalse(resultado.simulaciones[0].acepta)
        self.assertEqual(resultado.simulaciones[0].respuesta, "no")


class PruebasCoinciden(unittest.TestCase):
    def test_coinciden_detecta_desacuerdo(self):
        de_acuerdo = ResultadoSimulacion("x", (True, []), (True, []), (True, []))
        en_conflicto = ResultadoSimulacion("x", (True, []), (False, []), (True, []))
        self.assertTrue(de_acuerdo.coinciden)
        self.assertFalse(en_conflicto.coinciden)


class PruebasCodigosDeSalida(unittest.TestCase):
    def _correr(self, argv):
        salida = io.StringIO()
        with redirect_stdout(salida):
            codigo = main.main(argv)
        return codigo, salida.getvalue()

    def test_cero_cuando_todo_va_bien(self):
        ruta = archivo_temporal("a\n(a|b)*abb(a|b)*\n")
        self.addCleanup(os.remove, ruta)
        codigo, texto = self._correr([ruta, "-w", "abb", "--sin-imagenes"])
        self.assertEqual(codigo, 0)
        self.assertIn("=> w SÍ pertenece a L(r):  SÍ", texto)

    def test_uno_cuando_hay_una_linea_con_error(self):
        ruta = archivo_temporal("(a|b\n(a|b)*abb\n")
        self.addCleanup(os.remove, ruta)
        codigo, texto = self._correr([ruta, "-w", "abb", "--sin-imagenes"])
        self.assertEqual(codigo, 1)
        self.assertIn("ERROR:", texto)

    def test_dos_cuando_el_archivo_no_existe(self):
        codigo, _ = self._correr(["no_existe_int_123.txt", "--sin-imagenes"])
        self.assertEqual(codigo, 2)

    def test_ejemplo_del_enunciado_por_linea(self):
        ruta = archivo_temporal("(b|b)*abb(a|b)*;babbaaaa,ba\n")
        self.addCleanup(os.remove, ruta)
        codigo, texto = self._correr([ruta, "--sin-imagenes"])
        self.assertEqual(codigo, 0)
        self.assertIn("=> w SÍ pertenece a L(r):  SÍ", texto)
        self.assertIn("=> w NO pertenece a L(r):  NO", texto)


if __name__ == "__main__":
    unittest.main()
