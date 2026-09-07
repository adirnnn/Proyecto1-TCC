"""fase 2: de la expresión en postfija a un AFN, con el algoritmo de thompson.

thompson arma el AFN de abajo hacia arriba usando **fragmentos**. un fragmento
es un mini-autómata con exactamente un estado de entrada y uno de salida:

    símbolo a        (i) --a--> (f)
    ε                (i) --ε--> (f)

    concatenación    f1.fin --ε--> f2.inicio
    r·s              entrada = f1.inicio, salida = f2.fin

    unión            nuevos inicio y fin:
    r|s                  inicio --ε--> r.inicio,  inicio --ε--> s.inicio
                         r.fin  --ε--> fin,       s.fin  --ε--> fin

    cerradura        nuevos inicio y fin:
    r*                   inicio --ε--> r.inicio,  inicio --ε--> fin
                         r.fin  --ε--> r.inicio,  r.fin  --ε--> fin

    una o más        como la cerradura pero SIN "inicio --ε--> fin":
    r+                   inicio --ε--> r.inicio
                         r.fin  --ε--> r.inicio,  r.fin  --ε--> fin

    opcional         nuevos inicio y fin:
    r?                   inicio --ε--> r.inicio,  inicio --ε--> fin
                         r.fin  --ε--> fin

se recorre la lista postfija con una **pila de fragmentos**: un símbolo apila un
fragmento nuevo; un operador saca sus operandos, los combina y apila el
resultado. al final debe quedar exactamente un fragmento: ese es el AFN.

``+`` y ``?`` se construyen directo (cada uno su fragmento), sin reescribir la
expresión a ``r·r*`` ni ``r|ε``.

invariantes que se conservan (y que las pruebas verifican):

* hay exactamente **un** estado de aceptación y **no** tiene transiciones
  salientes;
* el estado inicial no tiene transiciones entrantes;
* cada símbolo aporta 2 estados; cada ``* + ? |`` aporta 2 más; la
  concatenación no aporta estados.
"""

from automata import AFN, Estado
from errores import ErrorRegex
from shunting_yard import CONCAT
from simbolos import EPSILON
from tokenizador import ESTRELLA, MAS, OPCIONAL, SIMBOLO, UNION


class _Fragmento:
    """trozo de AFN con un único estado de entrada y uno de salida."""

    __slots__ = ("inicio", "fin")

    def __init__(self, inicio, fin):
        self.inicio = inicio
        self.fin = fin


class _Constructor:
    """construye el AFN. lleva su propio contador de estados (sin estado global)."""

    def __init__(self):
        self._siguiente = 0
        self.estados = []

    def _nuevo_estado(self):
        estado = Estado(self._siguiente)
        self._siguiente += 1
        self.estados.append(estado)
        return estado

    # -- fragmentos básicos ------------------------------------------------
    def simbolo(self, valor):
        """(i) --valor--> (f).  ``valor`` puede ser un carácter o ``EPSILON``."""
        i, f = self._nuevo_estado(), self._nuevo_estado()
        i.agregar_transicion(valor, f)
        return _Fragmento(i, f)

    def concatenar(self, f1, f2):
        f1.fin.agregar_transicion(EPSILON, f2.inicio)
        return _Fragmento(f1.inicio, f2.fin)

    def unir(self, f1, f2):
        i, f = self._nuevo_estado(), self._nuevo_estado()
        i.agregar_transicion(EPSILON, f1.inicio)
        i.agregar_transicion(EPSILON, f2.inicio)
        f1.fin.agregar_transicion(EPSILON, f)
        f2.fin.agregar_transicion(EPSILON, f)
        return _Fragmento(i, f)

    def cerradura(self, frag):
        i, f = self._nuevo_estado(), self._nuevo_estado()
        i.agregar_transicion(EPSILON, frag.inicio)
        i.agregar_transicion(EPSILON, f)
        frag.fin.agregar_transicion(EPSILON, frag.inicio)
        frag.fin.agregar_transicion(EPSILON, f)
        return _Fragmento(i, f)

    def una_o_mas(self, frag):
        i, f = self._nuevo_estado(), self._nuevo_estado()
        i.agregar_transicion(EPSILON, frag.inicio)
        frag.fin.agregar_transicion(EPSILON, frag.inicio)
        frag.fin.agregar_transicion(EPSILON, f)
        return _Fragmento(i, f)

    def opcional(self, frag):
        i, f = self._nuevo_estado(), self._nuevo_estado()
        i.agregar_transicion(EPSILON, frag.inicio)
        i.agregar_transicion(EPSILON, f)
        frag.fin.agregar_transicion(EPSILON, f)
        return _Fragmento(i, f)

    # -- recorrido de la postfija ----------------------------------------
    def construir(self, postfix):
        if not postfix:
            raise ErrorRegex("no hay nada que construir: la expresión postfija "
                             "está vacía.")

        pila = []
        for token in postfix:
            if token.tipo == SIMBOLO:
                pila.append(self.simbolo(token.valor))
            elif token.tipo == CONCAT:
                derecho = self._sacar(pila, "·")
                izquierdo = self._sacar(pila, "·")
                pila.append(self.concatenar(izquierdo, derecho))
            elif token.tipo == UNION:
                derecho = self._sacar(pila, "|")
                izquierdo = self._sacar(pila, "|")
                pila.append(self.unir(izquierdo, derecho))
            elif token.tipo == ESTRELLA:
                pila.append(self.cerradura(self._sacar(pila, "*")))
            elif token.tipo == MAS:
                pila.append(self.una_o_mas(self._sacar(pila, "+")))
            elif token.tipo == OPCIONAL:
                pila.append(self.opcional(self._sacar(pila, "?")))
            else:
                raise ErrorRegex("token inesperado en la postfija: %r" % (token,))

        if len(pila) != 1:
            raise ErrorRegex(
                "la expresión postfija no genera un solo autómata: quedaron %d "
                "fragmentos sueltos." % len(pila))
        return _renumerar(pila[0])

    @staticmethod
    def _sacar(pila, operador):
        if not pila:
            raise ErrorRegex("el operador '%s' no tiene operando (expresión mal "
                             "formada)." % operador)
        return pila.pop()


def _renumerar(fragmento):
    """renumera los estados en orden BFS desde el inicial (q0, q1, q2, ...).

    solo es cosmético: hace que los reportes y los grafos se lean en el mismo
    orden en que se recorre el autómata.
    """
    orden = []
    vistos = {id(fragmento.inicio)}
    cola = [fragmento.inicio]
    while cola:
        actual = cola.pop(0)
        orden.append(actual)
        for _, destino in actual.transiciones:
            if id(destino) not in vistos:
                vistos.add(id(destino))
                cola.append(destino)

    for numero, estado in enumerate(orden):
        estado.numero = numero
    return AFN(orden, fragmento.inicio, fragmento.fin)


def construir_afn(postfix):
    """de la lista de ``Token`` en postfija al ``AFN`` de thompson."""
    return _Constructor().construir(postfix)


def afn_de_expresion(expresion):
    """atajo: de la cadena de la expresión directamente al ``AFN``."""
    from shunting_yard import convertir
    from tokenizador import tokenizar
    return construir_afn(convertir(tokenizar(expresion)))
