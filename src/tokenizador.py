"""fase 1a: partir la expresión regular en piezas (tokens).

el tokenizador recorre la cadena carácter por carácter y produce una lista de
tokens. cada token tiene:

* ``tipo``: qué clase de pieza es (un símbolo del alfabeto, un paréntesis, un
  operador...).
* ``valor``: para un símbolo, el carácter en sí, el objeto ``EPSILON`` (si el
  carácter era ``ε``), o un ``frozenset`` de caracteres (si es una **clase**
  ``[...]``: "cualquiera de estos"); para los demás, el propio carácter
  especial.
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

extensiones (no las pide el enunciado, pero las necesitan expresiones reales
como las clases de caracteres usadas en el examen -URLs, identificadores-):

* **clase de caracteres** ``[...]``: equivale a "cualquiera de estos símbolos"
  (como una unión de un solo carácter). admite **rangos** ``x-y`` (por ejemplo
  ``[a-z]``, ``[A-Z0-9_]``); un ``-`` al principio, al final, o escapado
  (``\\-``), es el guion literal. dentro de la clase también valen los
  escapes: ``\\]`` es el corchete que cierra como símbolo, ``\\\\`` la barra
  invertida, ``\\s`` el espacio en blanco (ver abajo). una clase sin ``]`` que
  la cierre, o vacía ``[]``, es un error.
* ``\\s`` (fuera o dentro de una clase) representa **espacio en blanco**:
  equivale a la clase ``[ \\t]`` (espacio y tabulador).
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

# escapes que representan más de un carácter (una mini-clase), en vez de uno
# solo. por ahora el único es \s = espacio en blanco = espacio y tabulador.
ESCAPES_CLASE = {"s": " \t"}


def _leer_clase(expresion, apertura):
    """lee la clase ``[...]`` que empieza en ``apertura`` (donde está el ``[``).

    devuelve ``(frozenset_de_caracteres, indice_justo_despues_del_']')``.
    dentro de la clase valen los mismos escapes que fuera (``\\]``, ``\\\\``,
    ``\\s``...); un ``-`` que no sea el primero, el último, ni una barra
    escapada, forma un **rango** con el carácter anterior y el siguiente.
    """
    n = len(expresion)
    i = apertura + 1
    # cada elemento es (caracter, es_literal_forzado); "forzado" = vino de un
    # escape, así que un '-' escapado nunca se interpreta como rango.
    miembros = []

    while i < n and expresion[i] != "]":
        c = expresion[i]
        if c == "\\":
            if i + 1 >= n:
                raise ErrorSimbolo(
                    "la clase de caracteres que empieza en la posición %d "
                    "termina con '\\' sin nada que escapar." % apertura)
            escapado = expresion[i + 1]
            if escapado in ESCAPES_CLASE:
                miembros.extend((ch, True) for ch in ESCAPES_CLASE[escapado])
            else:
                miembros.append((ESCAPES.get(escapado, escapado), True))
            i += 2
            continue
        miembros.append((c, False))
        i += 1

    if i >= n:
        raise ErrorSimbolo(
            "la clase de caracteres que empieza en la posición %d nunca "
            "cierra con ']'." % apertura)
    if not miembros:
        raise ErrorSimbolo(
            "la clase de caracteres '[]' en la posición %d está vacía." % apertura)

    caracteres = set()
    j = 0
    while j < len(miembros):
        caracter, forzado = miembros[j]
        hay_rango = (j + 2 < len(miembros) and not forzado
                    and miembros[j + 1] == ("-", False)
                    and not miembros[j + 2][1])
        if hay_rango:
            inicio, fin = caracter, miembros[j + 2][0]
            if ord(inicio) > ord(fin):
                raise ErrorSimbolo(
                    "rango inválido '%s-%s' en la clase de la posición %d "
                    "(el primero debe ir antes que el segundo)."
                    % (inicio, fin, apertura))
            caracteres.update(chr(codigo) for codigo in
                              range(ord(inicio), ord(fin) + 1))
            j += 3
        else:
            caracteres.add(caracter)
            j += 1

    return frozenset(caracteres), i + 1  # i apunta al ']'; +1 para pasarlo


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
            if siguiente in ESCAPES_CLASE:
                # \s (fuera de una clase) -> "cualquiera de estos": una
                # mini-clase, igual que si se hubiera escrito [ \t].
                tokens.append(Token(SIMBOLO, frozenset(ESCAPES_CLASE[siguiente]), i))
            else:
                # \0 -> carácter nulo; \c (cualquier otro) -> la letra c
                # literal, incluso si c es un metacarácter o la propia 'ε'.
                valor = ESCAPES.get(siguiente, siguiente)
                tokens.append(Token(SIMBOLO, valor, i))
            i += 2
            continue

        if c == "[":
            caracteres, siguiente_indice = _leer_clase(expresion, i)
            tokens.append(Token(SIMBOLO, caracteres, i))
            i = siguiente_indice
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
    if isinstance(valor, frozenset):
        return "[%s]" % "".join(sorted(valor))
    if valor == "\x00":
        return "\\0"
    return valor
