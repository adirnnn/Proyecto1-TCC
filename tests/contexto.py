"""agrega ``src/`` (y la raíz del proyecto) al ``sys.path``.

así cada archivo de pruebas puede importar los módulos por su nombre simple
(``from simbolos import EPSILON``). cada archivo de pruebas empieza con:

    import contexto  # noqa: F401
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")

for _ruta in (SRC, RAIZ):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
