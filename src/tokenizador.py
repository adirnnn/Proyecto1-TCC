"""fase 1a: partir la expresión regular en piezas (tokens).

el tokenizador recorre la cadena carácter por carácter y produce una lista de
tokens. cada token tiene:

* ``tipo``: qué clase de pieza es (un símbolo del alfabeto, un paréntesis, un
  operador...).
* ``valor``: para un símbolo, el carácter en sí (o el objeto ``EPSILON`` si el
  carácter era ``ε``); para los demás, el propio carácter especial.
* ``posicion``: el índice donde empieza la pieza en la cadena original. sirve
  para que los mensajes de error digan "en la posición N".

reglas:

* solo 7 caracteres son especiales: ``( ) | * + ? \\``. cualquier otro carácter
  es un símbolo del alfabeto (letras, dígitos, espacios, tildes, unicode, el
  carácter nulo...). aquí no se ignora ni se descarta nada.
* ``\\`` escapa al carácter siguiente: ``\\*`` es el asterisco como símbolo,
  ``\\|`` la barra como símbolo, ``\\\\`` la barra invertida como símbolo,
  ``\\ε`` la letra griega como símbolo normal. ``\\0`` es el carácter nulo
  (u+0000).
* si la expresión termina con ``\\`` suelto es un error (``ErrorSimbolo``).
* ``ε`` (sin escapar) representa la transición vacía: su token es un símbolo
  cuyo ``valor`` es el objeto ``EPSILON``.
"""

from collections import namedtuple

from errores import ErrorSimbolo
from simbolos import EPSILON, EPSILON_ENTRADA, ESCAPES

# tipos de token.
SIMBOLO = "SIMBOLO"      # una letra del alfabeto (o EPSILON)
LPAREN = "LPAREN"        # (
RPAREN = "RPAREN"        # )
UNION = "UNION"          # |
ESTRELLA = "ESTRELLA"    # *
MAS = "MAS"              # +
OPCIONAL = "OPCIONAL"    # ?

# tokens unarios postfijos (van después de su operando).
UNARIOS = frozenset({ESTRELLA, MAS, OPCIONAL})

Token = namedtuple("Token", ["tipo", "valor", "posicion"])

# de carácter especial a tipo de token.
_TIPO_DE_CARACTER = {
    "(": LPAREN,
    ")": RPAREN,
    "|": UNION,
    "*": ESTRELLA,
    "+": MAS,
    "?": OPCIONAL,
}


def tokenizar(expresion):
    """convierte la cadena de la expresión en una lista de ``Token``.

    devuelve una lista vacía si la expresión está vacía; la validación de "no
    puede estar vacía" la hace la siguiente fase (shunting yard).
    """
    tokens = []
    i = 0
    n = len(expresion)

    while i < n:
        c = expresion[i]

        if c == "\\":
            if i + 1 >= n:
                raise ErrorSimbolo(
                    "la expresión termina con '\\' pero falta el carácter que "
                    "debería escapar (posición %d)." % i)
            siguiente = expresion[i + 1]
            # \0 -> carácter nulo; \c (cualquier otro) -> la letra c literal,
            # incluso si c es un metacarácter o la propia 'ε'.
            valor = ESCAPES.get(siguiente, siguiente)
            tokens.append(Token(SIMBOLO, valor, i))
            i += 2
            continue

        tipo_especial = _TIPO_DE_CARACTER.get(c)
        if tipo_especial is not None:
            tokens.append(Token(tipo_especial, c, i))
        elif c == EPSILON_ENTRADA:
            tokens.append(Token(SIMBOLO, EPSILON, i))
        else:
            # cualquier otro carácter es un símbolo del alfabeto.
            tokens.append(Token(SIMBOLO, c, i))
        i += 1

    return tokens


def mostrar_valor(valor):
    """texto legible de un ``valor`` de token, para mensajes y reportes."""
    if valor is EPSILON:
        return "ε"
    if valor == "\x00":
        return "\\0"
    return valor
