"""pruebas del incremento 1: lectura del archivo de expresiones."""

import os
import tempfile
import unittest

import contexto  # noqa: F401

import main
from errores import ErrorArchivo


class PruebasLeerLineas(unittest.TestCase):
    def _archivo(self, contenido):
        descriptor, ruta = tempfile.mkstemp(suffix=".txt")
        os.close(descriptor)
        with open(ruta, "w", encoding="utf-8", newline="") as archivo:
            archivo.write(contenido)
        self.addCleanup(os.remove, ruta)
        return ruta

    def test_omite_vacias_y_comentarios(self):
        ruta = self._archivo("a\n\n   \n# comentario\nb|c\n")
        lineas = main.leer_lineas(ruta)
        self.assertEqual([texto for _, texto in lineas], ["a", "b|c"])

    def test_conserva_el_numero_de_linea_original(self):
        ruta = self._archivo("# nota\na\n")
        self.assertEqual(main.leer_lineas(ruta), [(2, "a")])

    def test_tolera_finales_de_linea_windows_y_sin_salto_final(self):
        ruta = self._archivo("a|b\r\n(a|b)*")
        self.assertEqual([texto for _, texto in main.leer_lineas(ruta)],
                         ["a|b", "(a|b)*"])

    def test_archivo_inexistente(self):
        with self.assertRaises(ErrorArchivo):
            main.leer_lineas("no_existe_este_archivo_12345.txt")

    def test_una_carpeta_no_es_un_archivo(self):
        with self.assertRaises(ErrorArchivo):
            main.leer_lineas(tempfile.gettempdir())


class PruebasEjecucion(unittest.TestCase):
    def test_main_devuelve_cero_con_un_archivo_valido(self):
        descriptor, ruta = tempfile.mkstemp(suffix=".txt")
        os.close(descriptor)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("a\n(a|b)*abb\n")
        self.addCleanup(os.remove, ruta)
        # --sin-imagenes: la ejecución completa se prueba en test_integracion;
        # aquí solo interesa el código de salida.
        self.assertEqual(main.main([ruta, "-w", "abb", "--sin-imagenes"]), 0)

    def test_main_devuelve_dos_si_el_archivo_no_existe(self):
        # -w evita que main pida la cadena por teclado durante la prueba.
        self.assertEqual(main.main(["no_existe_98765.txt", "-w", "x"]), 2)


if __name__ == "__main__":
    unittest.main()
