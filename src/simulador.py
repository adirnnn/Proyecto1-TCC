"""fase 4: simular la cadena ``w`` sobre el AFN y sobre los AFD.

el enunciado pide responder con **"sí"** si ``w ∈ L(r)`` y **"no"** si no.

* **AFN**: se trabaja con **conjuntos de estados** (el AFN puede estar en varios
  a la vez). se parte de la cerradura ε del estado inicial y, por cada símbolo
  de ``w``, se calcula ``cerradura_epsilon(mover(actuales, simbolo))``. se
  acepta si al terminar el conjunto contiene el estado de aceptación.

* **AFD** (y el AFD minimizado, que es un AFD): se sigue **un solo estado**. si
  el símbolo no pertenece al alfabeto, o si ``delta`` no está definida para
  ``(estado, simbolo)``, se rechaza de inmediato. se acepta si el estado final
  es de aceptación.

la cadena vacía (``""``) no entra al bucle: se responde según si el estado
inicial (o su cerradura ε, en el AFN) ya es de aceptación.

cada función devuelve ``(acepta, pasos)``: ``acepta`` es un ``bool`` y ``pasos``
es la traza legible que el programa puede imprimir para mostrar la simulación.
"""

from subconjuntos import cerradura_epsilon, mover

SI = "sí"
NO = "no"


def respuesta(acepta):
    """``True`` -> ``"sí"``; ``False`` -> ``"no"``."""
    return SI if acepta else NO


def _conjunto_a_texto(estados):
    if not estados:
        return "{} (vacío)"
    return "{%s}" % ", ".join(e.nombre for e in sorted(estados,
                                                       key=lambda e: e.numero))


def simular_afn(afn, cadena):
    """simula ``cadena`` sobre el ``AFN`` usando conjuntos de estados."""
    pasos = []
    actuales = cerradura_epsilon({afn.inicial})
    pasos.append("cerradura-ε del inicial: %s" % _conjunto_a_texto(actuales))

    for simbolo in cadena:
        siguientes = cerradura_epsilon(mover(actuales, simbolo))
        pasos.append("leer %r -> %s" % (simbolo, _conjunto_a_texto(siguientes)))
        actuales = siguientes
        if not actuales:
            pasos.append("conjunto vacío: se rechaza sin leer el resto")
            break

    acepta = afn.aceptacion in actuales
    return acepta, pasos


def simular_afd(afd, cadena):
    """simula ``cadena`` sobre un ``AFD`` (sirve igual para el AFD minimizado)."""
    pasos = []
    actual = afd.inicial
    pasos.append("estado inicial: %s" % afd.nombre(actual))

    for simbolo in cadena:
        if simbolo not in afd.alfabeto:
            pasos.append("leer %r -> el símbolo no pertenece al alfabeto: se "
                         "rechaza" % simbolo)
            return False, pasos
        siguiente = afd.transicion(actual, simbolo)
        if siguiente is None:
            pasos.append("leer %r -> no hay transición definida: se rechaza"
                         % simbolo)
            return False, pasos
        pasos.append("leer %r -> %s" % (simbolo, afd.nombre(siguiente)))
        actual = siguiente

    return afd.es_aceptacion(actual), pasos


def acepta_afn(afn, cadena):
    """solo el ``bool`` de la simulación del AFN."""
    return simular_afn(afn, cadena)[0]


def acepta_afd(afd, cadena):
    """solo el ``bool`` de la simulación del AFD."""
    return simular_afd(afd, cadena)[0]
