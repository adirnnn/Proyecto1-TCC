# Proyecto 1: Teoría de la Computación

de una **expresión regular** en notación infija a un **AFN** (thompson), a un
**AFD** (construcción de subconjuntos), a un **AFD mínimo** (refinamiento de
particiones), y simulación de una cadena `w` en los tres autómatas para
responder **sí** / **no** según si `w` pertenece al lenguaje de la expresión.

por cada expresión el programa:

1. convierte la notación **infix → postfix** con *shunting yard* (con
   concatenación explícita);
2. construye el **AFN** con el algoritmo de **thompson**;
3. convierte el AFN en **AFD** por **construcción de subconjuntos**;
4. **minimiza** el AFD por **refinamiento de particiones**;
5. **simula** `w` en el AFN, en el AFD y en el AFD minimizado, y responde
   **sí** o **no**;
6. genera una **imagen** (`.svg`) y el archivo **DOT** (`.dot`) de cada
   autómata, mostrando el estado inicial, los estados normales, los estados de
   aceptación y las transiciones con sus símbolos (ε incluido).

el programa lee un archivo de texto con **una expresión regular por línea** y
procesa todas; una línea con error se reporta y no detiene a las demás.

los cinco algoritmos están implementados a mano. **no se usa ninguna librería
externa**: todo es biblioteca estándar de python, incluida la generación de las
imágenes SVG.

---

## requisitos e instalación

- **python 3.10 o superior** (probado en 3.11).
- no hay dependencias. no hace falta `pip install` nada.

```bash
git clone <url-del-repositorio>
cd Proyecto1TCC
```

## ejecución

```bash
python main.py expresiones.txt -w babbaaaa
python main.py expresiones.txt -w abb -w ""        # -w "" es la cadena vacía
python main.py expresiones.txt --sin-imagenes --detalle
python main.py expresiones.txt -s imagenes --tabla
python main.py -r "(a|b)*abb(a|b)*" -w babbaaaa    # sin archivo
```

el archivo es opcional si se usa `-r`; se pueden combinar (las expresiones de
`-r` van primero y las del archivo siguen la numeración).

| opción | qué hace |
|---|---|
| `-r`, `--regex` | expresión regular escrita directamente aquí, sin archivo. se puede repetir. el texto se toma **tal cual**: `;` y `#` son símbolos normales. |
| `-w`, `--cadena` | cadena `w` a evaluar. se puede repetir: `-w abb -w ba`. |
| `-s`, `--salida` | carpeta donde se guardan los grafos (por defecto `salida`). |
| `--sin-imagenes` | no genera archivos SVG ni DOT (solo consola). |
| `-d`, `--detalle` | muestra la traza paso a paso de cada simulación. |
| `-t`, `--tabla` | muestra las tablas de transiciones de los AFD. |

si no se pasa `-w` y una expresión no trae sus propias cadenas (ver `;` abajo),
el programa pide la cadena `w` por teclado.

**códigos de salida:** `0` todo bien · `1` alguna línea con error o desacuerdo
entre autómatas · `2` no se pudo leer el archivo.

los grafos quedan en `salida/<nn>_<expresión>/` con los nombres `afn.svg`,
`afd_subconjuntos.svg` y `afd_minimizado.svg` (cada uno con su `.dot`).

## formato del archivo de entrada

una expresión regular **por línea**:

```
(a|b)*abb(a|b)*
(a*|b*)+
```

reglas:

- las **líneas vacías** o con solo espacios se **omiten** (no son un error);
- las líneas que empiezan con `#` son **comentarios** y también se omiten;
- se toleran los finales de línea de windows (`\r\n`) y un archivo **sin salto
  de línea final**;
- el archivo debe estar guardado en **UTF-8** (para poder escribir `ε`);
- **opcional**: después de un `;` se pueden listar cadenas de prueba separadas
  por coma; esas cadenas tienen prioridad sobre la que se pase con `-w`. una
  cadena vacía entre comas, o al final, significa la **cadena vacía**:

```
(a|b)*abb(a|b)*;babbaaaa,abb,ba,
```

si una expresión necesita usar `;` o empezar con `#` como símbolos del alfabeto,
se pasa con `-r` en lugar de por archivo: ahí el texto se toma tal cual.

en el repositorio están [`expresiones.txt`](expresiones.txt) y
[`expresiones_invalidas.txt`](expresiones_invalidas.txt) (para ver el manejo de
errores).

## formato de salida

por cada expresión se imprime: la postfija, el alfabeto, un resumen del AFN, del
AFD por subconjuntos y del AFD minimizado, las rutas de las imágenes y, por cada
cadena `w`, el veredicto en cada autómata más la línea
`=> w SÍ/NO pertenece a L(r)`. si los tres autómatas no coinciden, se marca con
`*** ATENCIÓN ***` (indica un error).

cuando el AFD minimizado necesitó un **estado pozo** para quedar completo, se
avisa justo debajo de su resumen. eso explica los casos en los que el AFD
minimizado tiene un estado **más** que el de subconjuntos (ver
[minimización](#4-minimización-srcminimizacionpy)): el de subconjuntos es
*parcial* y el mínimo se entrega *completo*.

---

## gramática soportada

| operador | significado | precedencia |
|---|---|---|
| `*` | cerradura de kleene (cero o más) | 3 (la más alta) |
| `+` | una o más repeticiones *(extensión)* | 3 |
| `?` | cero o una repetición *(extensión)* | 3 |
| *(implícito)* | concatenación | 2 |
| `\|` | unión | 1 (la más baja) |
| `( )` | agrupación | — |
| `ε` | la cadena vacía (transición que no consume nada) | — |

- la **concatenación es implícita**: `ab` significa `a·b`. antes de aplicar
  shunting yard, el parser la vuelve **explícita** insertando un token interno
  `CONCAT` (no es ningún carácter, así que no se puede teclear por error).
- todos los operadores binarios son **asociativos por la izquierda**.
- `+` y `?` son **extensiones** (no las pide el enunciado). se construyen como
  fragmentos propios de thompson, sin reescribir la expresión ni complicar el
  resto del proyecto.
- **cualquier carácter** que no sea uno de los 7 metacaracteres `( ) | * + ? \`
  es un **símbolo del alfabeto**: letras, dígitos, espacios, tildes, unicode, el
  carácter nulo…
- `\` **escapa** al carácter siguiente: `\*` es el asterisco *como símbolo*,
  `\|` la barra como símbolo, `\\` la barra invertida como símbolo, `\ε` la
  letra griega como símbolo normal. `\0` es el **carácter nulo** (U+0000). si la
  expresión termina con un `\` suelto es un error.
- **no** se soportan clases de caracteres `[abc]`, comodín `.`, ni anclas. `.`
  es un símbolo normal.

### errores que se reportan (sin romper el programa)

expresión vacía, paréntesis desbalanceados, grupo vacío `()`, operador sin
operando (`*a`, `+a`), unión incompleta (`a|`, `|a`, `a||b`, `(a|)`), `\` al
final. cada mensaje indica la posición del problema.

---

## representación de epsilon

es importante no confundir cuatro cosas:

| concepto | qué es | cómo se representa aquí |
|---|---|---|
| **epsilon (ε)** | una transición que **no consume** ningún símbolo | el objeto único `EPSILON` de `src/simbolos.py`, con su **propio tipo** |
| **cadena vacía** | una cadena de longitud 0 | `""` (un `str` de python de largo 0) |
| **lenguaje vacío** | un lenguaje sin ninguna cadena | no aparece como valor; sería un AFD sin estados de aceptación alcanzables |
| **carácter nulo** | el carácter real `\0`, U+0000 | `"\x00"`, un símbolo del alfabeto como cualquier otro |

- en el **archivo de entrada** epsilon se escribe con la letra griega `ε`
  (U+03B5). se eligió porque es la notación matemática estándar y es muy
  improbable que forme parte del alfabeto de un lenguaje de prueba.
- **internamente** epsilon es `EPSILON`, un objeto singleton con tipo propio
  (`_Epsilon`). **no** es una cadena, así que ninguna letra —ni `"\x00"`, ni un
  espacio, ni un metacarácter escapado— puede ser igual a él. **tampoco** es
  `None`: `None`/"clave ausente" se reserva para "aquí no hay transición" en el
  AFD. así ε y "no hay transición" nunca se cruzan.
- en los **nombres de carpeta** se usa la forma segura `epsilon`.

---

## estructura del proyecto

```
Proyecto1TCC/
├── main.py                 interfaz de línea de comandos y presentación
├── src/
│   ├── simbolos.py         EPSILON (tipo propio), metacaracteres, escapes
│   ├── errores.py          jerarquía de errores reportables
│   ├── tokenizador.py      fase 1a: cadena -> lista de Token
│   ├── shunting_yard.py    fase 1b: validación + concatenación explícita + postfix
│   ├── automata.py         estructuras AFN (Estado) y AFD (delta como dict)
│   ├── thompson.py         fase 2: postfix -> AFN con pila de fragmentos
│   ├── subconjuntos.py     fase 3: cerradura ε, mover, AFN -> AFD
│   ├── minimizacion.py     fase 4: inalcanzables + refinamiento de particiones
│   ├── simulador.py        fase 5: simular w en el AFN y en los AFD
│   ├── grafo_svg.py        fase 6: AFN/AFD -> SVG (y DOT)
│   └── procesador.py       fase 7: leer el archivo y orquestar todo
├── tests/                  pruebas con unittest (biblioteca estándar)
├── expresiones.txt         archivo de ejemplo
├── expresiones_invalidas.txt   ejemplos de errores reportados
└── Proyecto_1-1.pdf        enunciado
```

### estructuras de datos principales

- **`Token(tipo, valor, posicion)`** — pieza de la expresión. `tipo` es
  `SIMBOLO`, `LPAREN`, `RPAREN`, `UNION`, `ESTRELLA`, `MAS`, `OPCIONAL` o el
  sintético `CONCAT`. `valor` de un `SIMBOLO` es el carácter (o `EPSILON`).
- **AFN** (`automata.py`) — lista de objetos `Estado`; cada `Estado` guarda sus
  transiciones salientes como pares `(simbolo | EPSILON, Estado)`. un solo
  estado inicial y —por thompson— un solo estado de aceptación **sin
  transiciones salientes**.
- **AFD** (`automata.py`) — estados enteros; `delta` es un diccionario
  `{(estado, simbolo): estado}`; una clave ausente significa "no hay
  transición" → rechazo. `aceptacion` es un conjunto. `descripciones` guarda de
  qué estados del AFN (o de qué grupo) salió cada estado; es solo informativo.

---

## cómo funciona cada algoritmo

### 1. shunting yard (`src/shunting_yard.py`)

primero **valida** la lista de tokens (paréntesis balanceados, todo operador con
sus operandos). luego **inserta la concatenación explícita**: entre dos piezas
pegadas (`ab`, `a(b|c)`, `a*b`) se mete un token `CONCAT`. finalmente aplica
**shunting yard** con una pila de operadores:

- un **operando** (símbolo) va directo a la salida;
- `(` se apila; `)` desapila hasta el `(`;
- un operador **binario** (`|`, `CONCAT`) desapila primero todos los de
  precedencia **mayor o igual** (asociatividad izquierda) y luego se apila;
- los **unarios** `* + ?` son postfijos y de máxima precedencia: salen de
  inmediato.

la salida es otra lista de `Token`, para que thompson conserve el tipo y la
posición de cada pieza.

### 2. thompson (`src/thompson.py`)

construye el AFN de abajo hacia arriba con **fragmentos** (un estado de entrada
y uno de salida por fragmento). se recorre la postfija con una **pila de
fragmentos**: un símbolo apila un fragmento nuevo; un operador saca sus
operandos, los combina y apila el resultado.

- **símbolo `a`**: `(i) --a--> (f)`; **ε**: `(i) --ε--> (f)`
- **concatenación**: `f1.fin --ε--> f2.inicio`
- **unión**: nuevos `i`,`f` con cuatro ε (hacia y desde cada rama)
- **cerradura `*`**: nuevos `i`,`f` con `i→cuerpo`, `i→f`, `cuerpo.fin→cuerpo`,
  `cuerpo.fin→f`
- **`+`**: como `*` pero **sin** `i→f` (obliga a pasar al menos una vez)
- **`?`**: `i→cuerpo`, `i→f`, `cuerpo.fin→f`

al final los estados se renumeran en orden BFS (solo cosmético). el AFN
resultante siempre tiene un único estado de aceptación sin transiciones
salientes y un inicial sin transiciones entrantes.

### 3. construcción de subconjuntos (`src/subconjuntos.py`)

cada estado del AFD es un **conjunto** (`frozenset`) de estados del AFN.

- `cerradura_epsilon(T)`: todo lo alcanzable desde `T` usando solo ε. es
  **iterativa** (con pila), así que los ciclos de ε no dan recursión infinita.
- `mover(T, a)`: todo lo alcanzable desde `T` leyendo exactamente `a` (sin
  cerradura).

se parte de `cerradura_epsilon({q0})` y por cada símbolo se calcula
`cerradura_epsilon(mover(T, a))`. los subconjuntos, al ser `frozenset`, sirven
de clave: el mismo conjunto no se numera dos veces. un estado del AFD acepta si
su subconjunto contiene el estado de aceptación del AFN. si el resultado es el
**conjunto vacío**, la transición **no se crea**: el AFD queda *parcial* (una
transición faltante = rechazo).

### 4. minimización (`src/minimizacion.py`)

refinamiento de particiones (moore):

1. se quitan los estados **inalcanzables** desde el inicial y se renumera;
2. se **completa** el AFD con un **estado pozo** interno (así `delta` está
   definida en todos los pares y "no hay transición" también es comparable);
3. partición inicial: **no aceptación** vs **aceptación** (los grupos vacíos se
   descartan → cubre "sin aceptación" y "inicial de aceptación");
4. se **refina**: dos estados siguen juntos solo si para *cada* símbolo sus
   transiciones caen en el mismo grupo; se repite hasta punto fijo;
5. cada grupo final es un estado del AFD mínimo; las transiciones se calculan
   con un representante del grupo; se preservan el inicial y la aceptación.

el AFD minimizado que se devuelve es siempre **completo** (el AFD mínimo
*completo*). para expresiones envueltas en `(a|b)*` el AFD de subconjuntos ya es
completo y no aparece ningún pozo; para expresiones como `abb` el mínimo tiene
un estado más que la versión "de libro" que se dibuja parcial. cuando eso pasa,
el programa lo dice en la consola para que no parezca un error:

```
AFD (minimizado)  : 5 estados | inicial: S0 | aceptación: {S3} | alfabeto: {a, b}
          nota: el AFD minimizado se entrega completo; se le
          agregó el estado pozo P para las transiciones que
          faltaban, así δ queda definida en todos los pares.
```

### 5. simulación (`src/simulador.py`)

- **AFN**: se avanza con **conjuntos de estados**. se parte de la cerradura ε
  del inicial y por cada símbolo se calcula `cerradura(mover(S, a))`. acepta si
  el conjunto final contiene el estado de aceptación.
- **AFD** (y AFD mínimo): se sigue **un solo estado**. si el símbolo no
  pertenece al alfabeto, o si `delta` no está definida, se rechaza de inmediato.

la cadena vacía no entra al bucle: se responde según si el inicial (o su
cerradura ε) ya acepta.

### 6. grafos SVG (`src/grafo_svg.py`)

los algoritmos no dibujan. el AFN/AFD se pasa a un **modelo neutro** `Grafo` y
de ahí a **texto SVG** (imagen) y a **texto DOT** (por si se quiere renderizar
con graphviz; no se ejecuta). el acomodo es por niveles BFS desde el inicial. el
estado inicial lleva una flecha que viene de la nada; los de aceptación se
dibujan con doble círculo; cada arista lleva su símbolo (ε incluido) y las
aristas paralelas se juntan con las etiquetas separadas por coma. los auto-lazos
suben por encima de su estado, así que el dibujo se baja lo necesario para que
ese arco no se recorte ni se cruce con el título.

---

## pruebas

se usa `unittest` de la biblioteca estándar (no requiere instalar nada):

```bash
python -m unittest discover -s tests -t tests
```

cobertura:

- **shunting yard**: precedencia, asociatividad, concatenación explícita,
  `(a|b)*abb(a|b)*`, `+` `?`, expresiones malformadas.
- **thompson**: cantidad de estados y de transiciones ε por operador, único
  estado de aceptación sin salidas, inicial sin entradas, numeración BFS.
- **subconjuntos**: cerradura ε con ciclos, `mover`, determinismo, subconjuntos
  no duplicados, AFD parcial, `ε`.
- **minimización**: inalcanzables, fusión de equivalentes, tamaños conocidos
  (`a*` → 1, `(a|b)*abb` → 4), idempotencia, casos degenerados (1 estado, sin
  aceptación, inicial de aceptación).
- **simulación**: casos del enunciado, cadena vacía, expresiones anulables,
  rechazo tras coincidencia parcial, símbolo fuera del alfabeto, `\0`, espacio.
- **integración**: leer el archivo (`\r\n`, sin salto final, duplicados,
  comentarios), una línea con error no detiene el archivo, códigos de salida,
  `-r` sin archivo y combinado con archivo, aviso del estado pozo.
- **equivalencia**: para un banco de ~20 expresiones y **todas** las cadenas
  cortas, el AFN, el AFD y el AFD minimizado dan el mismo veredicto; y para las
  que se traducen limpio, se compara además contra `re.fullmatch` de python.

---

## ejemplos

### salida en consola (recortada)

```
======================================================================
expresión 1 (infix): (b|b)*abb(a|b)*
----------------------------------------------------------------------
postfix : bb|*a·b·b·ab|*·
alfabeto: {a, b}
AFN: 22 estados | inicial: q0 | aceptación: q16 | alfabeto: {a, b}
AFD (subconjuntos): 7 estados | inicial: S0 | aceptación: {S4, S5, S6} | alfabeto: {a, b}
AFD (minimizado)  : 5 estados | inicial: S0 | aceptación: {S3} | alfabeto: {a, b}

simulando w = "babbaaaa"
  AFN             : sí
  AFD subconjuntos: sí
  AFD minimizado  : sí
  => w SÍ pertenece a L(r):  SÍ
```

### grafos generados

en [`salida/ejemplo/`](salida/ejemplo/) están los grafos de `(a|b)*abb(a|b)*`
como evidencia (se regeneran con `python main.py expresiones.txt`):
[`afn.svg`](salida/ejemplo/afn.svg),
[`afd_subconjuntos.svg`](salida/ejemplo/afd_subconjuntos.svg) y
[`afd_minimizado.svg`](salida/ejemplo/afd_minimizado.svg) (cada uno con su
`.dot`). abren en cualquier navegador.

### tamaños de algunos autómatas

| expresión | postfix | AFN | AFD (subconj.) | AFD mínimo |
|---|---|---|---|---|
| `a*` | `a*` | 4 | 2 | 1 |
| `abb` | `ab·b·` | 6 | 4 | 5 *(completo, con pozo)* |
| `a?b+` | `a?b+·` | 8 | 3 | 4 |
| `(a\|b)*abb` | `ab\|*a·b·b·` | 14 | 5 | 4 |
| `(a\|b)*abb(a\|b)*` | `ab\|*a·b·b·ab\|*·` | 22 | 9 | 4 |
| `(b\|b)*abb(a\|b)*` | `bb\|*a·b·b·ab\|*·` | 22 | 7 | 5 |

### resultados verificados

| expresión | cadena | ¿`w ∈ L(r)`? |
|---|---|---|
| `(a\|b)*abb(a\|b)*` | `babbaaaa`, `abb`, `aabbabb` | sí |
| `(a\|b)*abb(a\|b)*` | `ba`, `aaa`, `ε` | no |
| `(a*\|b*)+` | `aaabbb`, `ab`, `ε` | sí |
| `(a*\|b*)+` | `c` | no |
| `((ε\|a)\|b*)*` | `aab`, `ε` | sí |

---

## limitaciones conocidas

- **sin clases de caracteres `[abc]`, comodín `.` ni anclas.** solo unión,
  concatenación, cerradura, `+`, `?`, agrupación, ε y escapes.
- `;` en el archivo de entrada separa la expresión de las cadenas de prueba, y
  un `#` al inicio de línea es un comentario, así que **ninguno de los dos puede
  usarse ahí como símbolo del alfabeto**; con `-r` sí, porque ese texto se toma
  tal cual.
- el **acomodo del SVG** es sencillo (columnas por nivel BFS): para el AFN de
  ~22 estados queda apretado y algunas aristas se cruzan. el AFD y el AFD mínimo
  se leen bien.
- las imágenes se generan en **SVG** (vectorial, abre en cualquier navegador).
  si hace falta un PNG, cada grafo trae su `.dot` al lado:
  `dot -Tpng afn.dot -o afn.png` con graphviz instalado.
- el AFD minimizado se entrega **completo**; para lenguajes como `abb` eso da un
  estado (el pozo) más que la versión parcial de algunos libros.
- minimización por moore "ingenuo" `O(n²·|Σ|)` por iteración; suficiente para el
  tamaño de autómatas del curso, más lento que hopcroft en teoría.

---
