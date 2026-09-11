"""pruebas del incremento 1: lectura del archivo de expresiones."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

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


class PruebasExpresionEnLaLineaDeComandos(unittest.TestCase):
    """``-r`` permite dar la expresión sin tener que crear un archivo."""

    def _correr(self, argv):
        salida = io.StringIO()
        with redirect_stdout(salida):
            codigo = main.main(argv)
        return codigo, salida.getvalue()

    def test_una_expresion_sin_archivo(self):
        codigo, texto = self._correr(
            ["-r", "(b|b)*abb(a|b)*", "-w", "babbaaaa", "--sin-imagenes"])
        self.assertEqual(codigo, 0)
        self.assertIn("=> w SÍ pertenece a L(r):  SÍ", texto)

    def test_varias_expresiones_se_numeran_seguidas(self):
        codigo, texto = self._correr(
            ["-r", "a", "-r", "b", "-w", "a", "--sin-imagenes"])
        self.assertEqual(codigo, 0)
        self.assertIn("expresión 1 (infix): a", texto)
        self.assertIn("expresión 2 (infix): b", texto)

    def test_el_texto_se_toma_tal_cual(self):
        # con -r, ';' y '#' son símbolos del alfabeto (en el archivo no).
        codigo, texto = self._correr(
            ["-r", "a;b", "-w", "a;b", "--sin-imagenes"])
        self.assertEqual(codigo, 0)
        self.assertIn("=> w SÍ pertenece a L(r):  SÍ", texto)
        codigo, texto = self._correr(["-r", "#a", "-w", "#a", "--sin-imagenes"])
        self.assertEqual(codigo, 0)
        self.assertIn("=> w SÍ pertenece a L(r):  SÍ", texto)

    def test_el_archivo_sigue_la_numeracion_de_las_de_r(self):
        descriptor, ruta = tempfile.mkstemp(suffix=".txt")
        os.close(descriptor)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("b\n")
        self.addCleanup(os.remove, ruta)
        _, texto = self._correr(["-r", "a", ruta, "-w", "a", "--sin-imagenes"])
        self.assertIn("expresión 1 (infix): a", texto)
        self.assertIn("expresión 2 (infix): b", texto)

    def test_sin_archivo_y_sin_r_es_un_error_de_uso(self):
        # argparse escribe el uso en stderr y termina con SystemExit.
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                main.main(["--sin-imagenes"])


class PruebasNotaDelEstadoPozo(unittest.TestCase):
    """el AFD minimizado se entrega completo: hay que avisarlo cuando pasa."""

    def _correr(self, argv):
        salida = io.StringIO()
        with redirect_stdout(salida):
            main.main(argv)
        return salida.getvalue()

    def test_se_avisa_cuando_se_agrego_el_pozo(self):
        # 'abb' necesita pozo: el AFD por subconjuntos es parcial.
        texto = self._correr(["-r", "abb", "-w", "abb", "--sin-imagenes"])
        self.assertIn("estado pozo P", texto)

    def test_no_se_avisa_cuando_no_hizo_falta(self):
        # '(a|b)*abb(a|b)*' ya es completo: no debe aparecer la nota.
        texto = self._correr(
            ["-r", "(a|b)*abb(a|b)*", "-w", "abb", "--sin-imagenes"])
        self.assertNotIn("estado pozo P", texto)


if __name__ == "__main__":
    unittest.main()
