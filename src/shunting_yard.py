"""fase 1b: de la lista de tokens (infija) a notación postfija.

esta fase hace tres cosas, en este orden:

1. **validar** que la secuencia de tokens forme una expresión regular bien
   escrita (paréntesis balanceados, todo operador con sus operandos, etc.). se
   valida *antes* de tocar nada para que los mensajes de error hablen de lo que
   la persona realmente escribió.
2. **volver explícita la concatenación**: entre dos piezas que están
   simplemente pegadas (``ab``, ``a(b|c)``, ``a*b``...) se inserta un token
   sintético ``CONCAT``. no existe ningún carácter para concatenar, así que
   nadie puede escribirlo por error.
3. **shunting yard** (dijkstra): con una pila de operadores se pasa de infija a
   postfija.

precedencia, de mayor a menor (como pide el enunciado):

* ``* + ?``  -> 3   (unarios postfijos: ya vienen después de su operando, así
  que salen directo a la salida)
* concatenación -> 2
* ``|`` (unión) -> 1

todos los operadores binarios son asociativos por la izquierda: antes de apilar
uno se sacan de la pila los que tengan precedencia **mayor o igual**.

la salida es otra lista de ``Token`` (no una cadena) para que la siguiente fase
(thompson) conserve tipo y posición de cada pieza.
"""

from errores import ErrorExpresionVacia, ErrorOperador, ErrorParentesis
from tokenizador import (ESTRELLA, LPAREN, MAS, OPCIONAL, RPAREN, SIMBOLO,
                         UNION, Token, UNARIOS, mostrar_valor, tokenizar)

# token sintético de concatenación. no lo produce el tokenizador (no hay ningún
# carácter que le corresponda): lo inserta esta fase. el "·" es solo para poder
# mostrarlo de forma legible al imprimir la postfija.
CONCAT = "CONCAT"
CONCAT_TEXTO = "·"

# operadores binarios y su precedencia.
_PRECEDENCIA = {UNION: 1, CONCAT: 2}

# tipos de token que *terminan* un operando (algo puede concatenarse a su
# derecha) y tipos que *empiezan* un operando (algo puede concatenarse a su
# izquierda).
_TERMINA_OPERANDO = frozenset({SIMBOLO, RPAREN, ESTRELLA, MAS, OPCIONAL})
_EMPIEZA_OPERANDO = frozenset({SIMBOLO, LPAREN})


def validar(tokens):
    """revisa que ``tokens`` forme una expresión regular válida.

    lanza ``ErrorExpresionVacia``, ``ErrorParentesis`` o ``ErrorOperador`` con
    un mensaje que apunta a la posición del problema. si todo está bien devuelve
    la misma lista.
    """
    if not tokens:
        raise ErrorExpresionVacia("la expresión regular está vacía.")

    profundidad = 0
    anterior = None

    for token in tokens:
        tipo = token.tipo

        # al inicio, después de "(" y después de "|" se espera que empiece un
        # operando (un símbolo o un "(").
        espera_operando = anterior is None or anterior.tipo in (LPAREN, UNION)
        if espera_operando:
            if tipo in UNARIOS:
                if anterior is None:
                    raise ErrorOperador(
                        "la expresión empieza con el operador '%s' pero no hay "
                        "nada a lo que aplicarlo (posición %d)."
                        % (token.valor, token.posicion))
                raise ErrorOperador(
                    "el operador '%s' en la posición %d no tiene operando: "
                    "aparece justo después de '%s'."
                    % (token.valor, token.posicion, anterior.valor))
            if tipo == UNION:
                raise ErrorOperador(
                    "unión incompleta: falta el operando izquierdo del '|' "
                    "(posición %d)." % token.posicion)
            if tipo == RPAREN:
                if anterior is not None and anterior.tipo == LPAREN:
                    raise ErrorParentesis(
                        "grupo vacío '()' en la posición %d." % token.posicion)
                raise ErrorOperador(
                    "unión incompleta: falta el operando derecho del '|' antes "
                    "del ')' en la posición %d." % token.posicion)

        if tipo == LPAREN:
            profundidad += 1
        elif tipo == RPAREN:
            profundidad -= 1
            if profundidad < 0:
                raise ErrorParentesis(
                    "paréntesis desbalanceados: ')' de sobra en la posición %d."
                    % token.posicion)

        anterior = token

    if profundidad != 0:
        raise ErrorParentesis(
            "paréntesis desbalanceados: faltan %d paréntesis de cierre ')'."
            % profundidad)

    if anterior.tipo == UNION:
        raise ErrorOperador(
            "unión incompleta: la expresión termina con '|' (posición %d)."
            % anterior.posicion)

    return tokens


def insertar_concatenacion(tokens):
    """devuelve una lista nueva con un token ``CONCAT`` entre cada par de piezas
    que estaban simplemente pegadas.

    se inserta entre ``a`` y ``b`` cuando ``a`` termina un operando (un símbolo,
    un ')' o un unario ya aplicado) y ``b`` empieza otro (un símbolo o un '(').
    """
    resultado = []
    for indice, token in enumerate(tokens):
        resultado.append(token)
        if indice + 1 >= len(tokens):
            break
        siguiente = tokens[indice + 1]
        if token.tipo in _TERMINA_OPERANDO and siguiente.tipo in _EMPIEZA_OPERANDO:
            resultado.append(Token(CONCAT, CONCAT_TEXTO, token.posicion))
    return resultado


def a_postfix(tokens):
    """shunting yard sobre tokens que **ya** tienen la concatenación explícita.

    devuelve la lista de ``Token`` en orden postfijo.
    """
    salida = []
    pila = []

    for token in tokens:
        tipo = token.tipo

        if tipo == SIMBOLO:
            salida.append(token)

        elif tipo in UNARIOS:
            # postfijos y de máxima precedencia: ya están después de su
            # operando, así que salen de inmediato.
            salida.append(token)

        elif tipo == LPAREN:
            pila.append(token)

        elif tipo == RPAREN:
            while pila and pila[-1].tipo != LPAREN:
                salida.append(pila.pop())
            if not pila:
                raise ErrorParentesis(
                    "paréntesis desbalanceados: ')' sin '(' que le corresponda "
                    "(posición %d)." % token.posicion)
            pila.pop()  # descarta el "("

        elif tipo in (UNION, CONCAT):
            while (pila and pila[-1].tipo in (UNION, CONCAT)
                   and _PRECEDENCIA[pila[-1].tipo] >= _PRECEDENCIA[tipo]):
                salida.append(pila.pop())
            pila.append(token)

    while pila:
        token = pila.pop()
        if token.tipo == LPAREN:
            raise ErrorParentesis(
                "paréntesis desbalanceados: falta el ')' que cierra el '(' de "
                "la posición %d." % token.posicion)
        salida.append(token)

    return salida


def convertir(tokens):
    """pipeline completo de esta fase: tokens infijos -> tokens postfijos.

    valida, inserta la concatenación explícita y aplica shunting yard.
    """
    validar(tokens)
    return a_postfix(insertar_concatenacion(tokens))


def infix_a_postfix(expresion):
    """atajo cómodo: de la cadena de la expresión directamente a la postfija."""
    return convertir(tokenizar(expresion))


def postfix_a_texto(tokens):
    """une la lista postfija en una sola cadena legible (para imprimirla)."""
    piezas = []
    for token in tokens:
        if token.tipo == SIMBOLO:
            piezas.append(mostrar_valor(token.valor))
        elif token.tipo == CONCAT:
            piezas.append(CONCAT_TEXTO)
        else:
            piezas.append(token.valor)
    return "".join(piezas)
