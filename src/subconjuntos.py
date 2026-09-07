"""fase 3: de un AFN a un AFD equivalente, por construcción de subconjuntos.

idea: cada estado del AFD es un **conjunto** de estados del AFN -los estados en
los que el AFN "podría estar" a la vez-.

    cerradura_epsilon(T) = T más todo lo alcanzable desde T usando solo ε.
    mover(T, a)          = estados alcanzables desde T leyendo exactamente 'a'
                           (sin cerradura; eso se aplica después).

pseudocódigo (aho, sethi, ullman):

    inicial    = cerradura_epsilon({q0})
    pendientes = [inicial]
    mientras haya un subconjunto T sin procesar:
        para cada símbolo a del alfabeto:
            U = cerradura_epsilon(mover(T, a))
            si U no está vacío:
                si U es nuevo -> agregarlo a los estados y a pendientes
                delta[T, a] = U

* los subconjuntos se guardan como ``frozenset`` para que el mismo conjunto no
  se cree dos veces (son la clave del diccionario de identificadores).
* un estado del AFD es de aceptación si su subconjunto contiene el estado de
  aceptación del AFN.
* si ``U`` queda vacío, **no** se crea la transición: el AFD queda *parcial* y
  esa transición faltante significa rechazo. la minimización (fase 4) lo
  completa internamente con un estado pozo cuando lo necesita.

``cerradura_epsilon`` es iterativa (con pila), así que los ciclos de ε -por
ejemplo los que arma la cerradura de thompson- no provocan recursión infinita.
"""

from automata import AFD
from simbolos import EPSILON


def cerradura_epsilon(estados):
    """todos los estados alcanzables desde ``estados`` usando solo transiciones ε.

    incluye a los propios ``estados`` de partida. devuelve un ``frozenset``.
    """
    resultado = set(estados)
    pila = list(estados)
    while pila:
        actual = pila.pop()
        for simbolo, destino in actual.transiciones:
            if simbolo is EPSILON and destino not in resultado:
                resultado.add(destino)
                pila.append(destino)
    return frozenset(resultado)


def mover(estados, simbolo):
    """estados alcanzables desde ``estados`` consumiendo exactamente ``simbolo``.

    no aplica la cerradura ε (eso se hace aparte). devuelve un ``frozenset``.
    """
    destinos = set()
    for estado in estados:
        for etiqueta, destino in estado.transiciones:
            if etiqueta is not EPSILON and etiqueta == simbolo:
                destinos.add(destino)
    return frozenset(destinos)


def _describir(subconjunto):
    """texto '{q0, q1, q3}' de qué estados del AFN representa un estado del AFD."""
    return "{%s}" % ", ".join(e.nombre for e in sorted(subconjunto,
                                                       key=lambda e: e.numero))


def afn_a_afd(afn):
    """convierte el ``AFN`` en un ``AFD`` equivalente (parcial, sin estado pozo)."""
    alfabeto = sorted(afn.alfabeto)

    inicial = cerradura_epsilon({afn.inicial})
    identificador = {inicial: 0}
    subconjuntos = [inicial]        # subconjuntos[i] es el estado i del AFD
    pendientes = [inicial]
    transiciones = {}

    while pendientes:
        actual = pendientes.pop(0)
        origen = identificador[actual]
        for simbolo in alfabeto:
            destino = cerradura_epsilon(mover(actual, simbolo))
            if not destino:
                continue               # conjunto vacío: no hay transición
            if destino not in identificador:
                identificador[destino] = len(subconjuntos)
                subconjuntos.append(destino)
                pendientes.append(destino)
            transiciones[(origen, simbolo)] = identificador[destino]

    estados = list(range(len(subconjuntos)))
    aceptacion = {i for i, sub in enumerate(subconjuntos) if afn.aceptacion in sub}
    descripciones = {i: _describir(sub) for i, sub in enumerate(subconjuntos)}
    return AFD(estados, alfabeto, 0, aceptacion, transiciones, descripciones)


def afd_de_expresion(expresion):
    """atajo: de la cadena de la expresión directamente al ``AFD`` (parcial)."""
    from thompson import afn_de_expresion
    return afn_a_afd(afn_de_expresion(expresion))
