"""estructuras de datos de los autómatas: ``AFN`` y ``AFD``.

un autómata finito es la quíntupla ``(Q, Sigma, delta, q0, F)``. aquí:

* **AFN** (no determinista, el que arma thompson): ``Q`` es una lista de objetos
  ``Estado``; ``delta`` vive dentro de cada estado como una lista de pares
  ``(simbolo, destino)``; ``q0`` es ``inicial`` y ``F`` es un **único** estado
  ``aceptacion`` (invariante de thompson). una transición ε lleva como símbolo
  el objeto ``EPSILON`` de ``simbolos.py`` (nunca ``None`` ni una cadena, así no
  se confunde con un símbolo del alfabeto ni con "aquí no hay transición").

* **AFD** (determinista, el de subconjuntos y el minimizado): ``Q`` es una lista
  de enteros; ``delta`` es un diccionario ``{(estado, simbolo): estado}``; ``q0``
  es ``inicial`` y ``F`` es el conjunto ``aceptacion``. no hay transiciones ε.
  que falte una clave en ``delta`` significa "no hay transición" -> rechazo.

``descripciones`` (opcional en el AFD) guarda de dónde salió cada estado -por
ejemplo el subconjunto de estados del AFN, o el grupo de estados equivalentes
tras minimizar-. es solo informativo: se usa en los reportes y las imágenes.
"""

from simbolos import EPSILON


# ==========================================================================
# AFN
# ==========================================================================
class Estado:
    """estado de un AFN, con su lista de transiciones salientes."""

    def __init__(self, numero):
        self.numero = numero
        self.transiciones = []  # lista de (simbolo | EPSILON, Estado)

    @property
    def nombre(self):
        return "q%d" % self.numero

    def agregar_transicion(self, simbolo, destino):
        """agrega la transición ``(self, simbolo, destino)``.

        ``simbolo`` es un carácter del alfabeto o el objeto ``EPSILON``.
        """
        self.transiciones.append((simbolo, destino))

    def __repr__(self):
        return "Estado(%s)" % self.nombre


class Transicion:
    """vista de solo lectura de una transición del AFN (para reportes y dibujo)."""

    def __init__(self, origen, simbolo, destino):
        self.origen = origen
        self.simbolo = simbolo        # carácter del alfabeto o EPSILON
        self.destino = destino

    @property
    def es_epsilon(self):
        return self.simbolo is EPSILON

    def __repr__(self):
        etiqueta = "ε" if self.es_epsilon else self.simbolo
        return "%s --%s--> %s" % (self.origen.nombre, etiqueta, self.destino.nombre)


class AFN:
    """AFN de thompson: un estado inicial y un único estado de aceptación."""

    def __init__(self, estados, inicial, aceptacion):
        self.estados = list(estados)
        self.inicial = inicial
        self.aceptacion = aceptacion

    @property
    def alfabeto(self):
        """símbolos que etiquetan alguna transición (ε queda excluido)."""
        simbolos = set()
        for estado in self.estados:
            for simbolo, _ in estado.transiciones:
                if simbolo is not EPSILON:
                    simbolos.add(simbolo)
        return simbolos

    def transiciones(self):
        """todas las transiciones del AFN como objetos ``Transicion``."""
        return [Transicion(estado, simbolo, destino)
                for estado in self.estados
                for simbolo, destino in estado.transiciones]

    def es_aceptacion(self, estado):
        return estado is self.aceptacion

    def resumen(self):
        return ("AFN: %d estados | inicial: %s | aceptación: %s | alfabeto: {%s}"
                % (len(self.estados), self.inicial.nombre, self.aceptacion.nombre,
                   ", ".join(sorted(self.alfabeto))))


# ==========================================================================
# AFD
# ==========================================================================
class AFD:
    """AFD: ``delta`` como diccionario; clave faltante = no hay transición."""

    def __init__(self, estados, alfabeto, inicial, aceptacion, transiciones,
                 descripciones=None, estado_pozo=None):
        self.estados = list(estados)
        self.alfabeto = sorted(alfabeto)
        self.inicial = inicial
        self.aceptacion = set(aceptacion)
        self.transiciones = dict(transiciones)
        self.descripciones = dict(descripciones or {})
        # estado sumidero (trampa), si se agregó al completar el autómata.
        self.estado_pozo = estado_pozo

    def transicion(self, estado, simbolo):
        """destino de ``delta(estado, simbolo)`` o ``None`` si no está definida."""
        return self.transiciones.get((estado, simbolo))

    def es_aceptacion(self, estado):
        return estado in self.aceptacion

    def es_completo(self):
        """¿hay transición para cada par ``(estado, simbolo)`` del alfabeto?"""
        return all((estado, simbolo) in self.transiciones
                   for estado in self.estados for simbolo in self.alfabeto)

    def nombre(self, estado):
        """nombre visible del estado ('P' para el estado pozo)."""
        if self.estado_pozo is not None and estado == self.estado_pozo:
            return "P"
        return "S%d" % estado

    def descripcion(self, estado):
        return self.descripciones.get(estado, "")

    def transiciones_ordenadas(self):
        """lista ``[(origen, simbolo, destino)]`` ordenada, útil para imprimir."""
        return sorted(((origen, simbolo, destino)
                       for (origen, simbolo), destino in self.transiciones.items()),
                      key=lambda t: (t[0], str(t[1])))

    def tabla(self):
        """tabla de transiciones como texto (una fila por estado)."""
        encabezado = ["estado"] + list(self.alfabeto)
        filas = [encabezado]
        for estado in self.estados:
            marca = ""
            if estado == self.inicial:
                marca += "->"
            if self.es_aceptacion(estado):
                marca += "*"
            fila = [marca + self.nombre(estado)]
            for simbolo in self.alfabeto:
                destino = self.transicion(estado, simbolo)
                fila.append("-" if destino is None else self.nombre(destino))
            filas.append(fila)

        anchos = [max(len(fila[i]) for fila in filas) for i in range(len(encabezado))]
        return "\n".join("  ".join(celda.ljust(anchos[i]) for i, celda in enumerate(fila))
                         for fila in filas)

    def resumen(self):
        return ("AFD: %d estados | inicial: %s | aceptación: {%s} | alfabeto: {%s}"
                % (len(self.estados), self.nombre(self.inicial),
                   ", ".join(self.nombre(e) for e in sorted(self.aceptacion)),
                   ", ".join(self.alfabeto)))
