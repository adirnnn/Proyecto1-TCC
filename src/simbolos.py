"""símbolos y constantes que comparten todas las etapas del proyecto.

decisiones de notación (también explicadas en el readme):

* epsilon (la "transición vacía", la que no consume ninguna letra) se representa
  internamente con el objeto único ``EPSILON``, que tiene su propio tipo. no es
  una cadena, así que ninguna letra del alfabeto -ni el carácter nulo ``\\x00``,
  ni un espacio, ni un metacarácter escapado- puede ser igual a él. tampoco es
  ``None``, para no confundirlo con "aquí no hay transición".
* en el archivo de entrada, epsilon se escribe con la letra griega ``ε``
  (u+03b5).
* ``METACARACTERES``: los 7 caracteres con significado especial dentro de una
  expresión. cualquier otro carácter es un símbolo normal del alfabeto. para
  usar uno de estos 7 como símbolo normal se escapa con ``\\`` (por ejemplo
  ``\\*`` es el asterisco como letra).
"""


class _Epsilon:
    """tipo del marcador interno de epsilon; se usa como singleton ``EPSILON``."""

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def __repr__(self):
        return "EPSILON"

    def __str__(self):
        return "ε"


# marcador interno de la transición vacía. único, con tipo propio.
EPSILON = _Epsilon()

# cómo se escribe epsilon en el archivo de entrada.
EPSILON_ENTRADA = "ε"

# los 7 caracteres especiales de una expresión regular. todo lo demás es un
# símbolo del alfabeto (letras, dígitos, espacios, tildes, el carácter nulo...).
METACARACTERES = frozenset("()|*+?\\")

# escapes reconocidos después de ``\\``: ``\\0`` es el carácter nulo (u+0000).
# para cualquier otro carácter c, ``\\c`` significa "la letra c" (así se mete un
# metacarácter en el alfabeto); eso lo resuelve el tokenizador, no esta tabla.
ESCAPES = {"0": "\x00"}
