"""fase 5: de un AFD a un AFD mínimo equivalente.

método: **refinamiento de particiones** (moore).

1. se quitan los estados **inalcanzables** desde el inicial: no aportan nada al
   lenguaje. se renumera para que el inicial vuelva a ser el 0.
2. se **completa** el AFD con un **estado pozo** interno: para cada par
   ``(estado, simbolo)`` sin transición se agrega una que va al pozo, y el pozo
   va a sí mismo con cada símbolo. así ``delta`` está definida en todos los
   pares y "no hay transición" también es una conducta comparable entre estados.
3. **partición inicial** en dos grupos: estados de **aceptación** y de **no
   aceptación** (la cadena vacía ya los distingue). los grupos vacíos se
   descartan -así se cubren "sin estados de aceptación" y "el inicial es de
   aceptación"-.
4. se **refina**: dentro de un grupo, dos estados siguen juntos solo si para
   **cada** símbolo del alfabeto sus transiciones caen en el **mismo** grupo. si
   difieren, el grupo se parte. se repite hasta que la partición no cambie.
5. cada grupo final es un estado del AFD mínimo. como todos los estados de un
   grupo se comportan igual, se toma un representante para calcular las
   transiciones. se preservan el estado inicial y la aceptación.

decisión de diseño: el AFD minimizado que se devuelve es siempre **completo**
(el AFD mínimo *completo*). para lenguajes como ``abb`` esto da un estado más
que la versión "de libro" que se dibuja parcial; para las expresiones típicas
del curso -envueltas en ``(a|b)*``- el AFD de subconjuntos ya es completo y no
aparece ningún pozo (``(a|b)*abb`` -> 4 estados).
"""

import copy

from automata import AFD


# --------------------------------------------------------------------------
# paso 1: estados inalcanzables
# --------------------------------------------------------------------------
def estados_alcanzables(afd):
    """estados a los que se llega desde el inicial, en orden BFS."""
    orden = [afd.inicial]
    vistos = {afd.inicial}
    cola = [afd.inicial]
    while cola:
        actual = cola.pop(0)
        for simbolo in afd.alfabeto:
            destino = afd.transicion(actual, simbolo)
            if destino is not None and destino not in vistos:
                vistos.add(destino)
                orden.append(destino)
                cola.append(destino)
    return orden


def eliminar_inalcanzables(afd):
    """copia del AFD sin estados inalcanzables y renumerada (inicial = 0)."""
    orden = estados_alcanzables(afd)
    nuevo = {viejo: i for i, viejo in enumerate(orden)}

    transiciones = {}
    for viejo in orden:
        for simbolo in afd.alfabeto:
            destino = afd.transicion(viejo, simbolo)
            if destino is not None and destino in nuevo:
                transiciones[(nuevo[viejo], simbolo)] = nuevo[destino]

    aceptacion = {nuevo[v] for v in orden if afd.es_aceptacion(v)}
    descripciones = {nuevo[v]: afd.descripcion(v) for v in orden}
    pozo = nuevo[afd.estado_pozo] if afd.estado_pozo in nuevo else None
    return AFD(list(range(len(orden))), afd.alfabeto, 0, aceptacion,
               transiciones, descripciones, estado_pozo=pozo)


# --------------------------------------------------------------------------
# paso 2: completar con estado pozo
# --------------------------------------------------------------------------
def completar_con_pozo(afd):
    """agrega (si hace falta) el estado pozo que absorbe las transiciones
    faltantes.  modifica el AFD y devuelve el número del pozo, o ``None`` si ya
    era completo.
    """
    faltantes = [(estado, simbolo)
                 for estado in afd.estados
                 for simbolo in afd.alfabeto
                 if (estado, simbolo) not in afd.transiciones]
    if not faltantes:
        return None

    pozo = (max(afd.estados) + 1) if afd.estados else 0
    afd.estados.append(pozo)
    afd.estado_pozo = pozo
    afd.descripciones[pozo] = "{} (estado pozo)"
    for estado, simbolo in faltantes:
        afd.transiciones[(estado, simbolo)] = pozo
    for simbolo in afd.alfabeto:
        afd.transiciones[(pozo, simbolo)] = pozo
    return pozo


# --------------------------------------------------------------------------
# pasos 3 y 4: refinamiento de particiones
# --------------------------------------------------------------------------
def _particion_inicial(afd):
    no_finales = [e for e in afd.estados if not afd.es_aceptacion(e)]
    finales = [e for e in afd.estados if afd.es_aceptacion(e)]
    return [grupo for grupo in (no_finales, finales) if grupo]


def calcular_particiones(afd):
    """refina la partición hasta que deja de cambiar y devuelve los grupos."""
    particion = _particion_inicial(afd)

    while True:
        grupo_de = {estado: indice
                    for indice, grupo in enumerate(particion)
                    for estado in grupo}

        nueva = []
        for grupo in particion:
            por_firma = {}
            for estado in grupo:
                # firma: a qué grupo lo manda cada símbolo (el AFD ya es completo).
                firma = tuple(grupo_de[afd.transicion(estado, simbolo)]
                              for simbolo in afd.alfabeto)
                por_firma.setdefault(firma, []).append(estado)
            for subgrupo in sorted(por_firma.values(), key=min):
                nueva.append(subgrupo)

        if len(nueva) == len(particion):
            return nueva
        particion = nueva


# --------------------------------------------------------------------------
# paso 5: reconstruir el AFD mínimo
# --------------------------------------------------------------------------
def minimizar(afd):
    """devuelve un AFD mínimo equivalente (no modifica el original)."""
    trabajo = eliminar_inalcanzables(copy.deepcopy(afd))
    completar_con_pozo(trabajo)                       # ahora es completo

    particion = calcular_particiones(trabajo)
    # el grupo del estado inicial (estado 0) queda primero porque 0 es su menor.
    particion = sorted(particion, key=min)
    grupo_de = {estado: indice
                for indice, grupo in enumerate(particion)
                for estado in grupo}

    transiciones = {}
    for indice, grupo in enumerate(particion):
        representante = grupo[0]
        for simbolo in trabajo.alfabeto:
            destino = trabajo.transicion(representante, simbolo)
            if destino is not None:
                transiciones[(indice, simbolo)] = grupo_de[destino]

    aceptacion = {indice for indice, grupo in enumerate(particion)
                  if trabajo.es_aceptacion(grupo[0])}
    descripciones = {
        indice: "{%s}" % ", ".join(trabajo.nombre(e) for e in sorted(grupo))
        for indice, grupo in enumerate(particion)}
    pozo = (grupo_de.get(trabajo.estado_pozo)
            if trabajo.estado_pozo is not None else None)

    return AFD(list(range(len(particion))), trabajo.alfabeto,
               grupo_de[trabajo.inicial], aceptacion, transiciones,
               descripciones, estado_pozo=pozo)


def afd_minimo_de_expresion(expresion):
    """atajo: de la cadena de la expresión directamente al AFD mínimo."""
    from subconjuntos import afd_de_expresion
    return minimizar(afd_de_expresion(expresion))
