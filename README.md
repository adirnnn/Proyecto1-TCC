# proyecto 1 — teoría de la computación

de una **expresión regular** a un **afn** (thompson), a un **afd** (construcción
de subconjuntos), a un **afd mínimo** (refinamiento de particiones), y simulación
de una cadena `w` en los tres autómatas para responder **sí** / **no** según si
`w` pertenece al lenguaje de la expresión.

el programa lee un archivo de texto con **una expresión regular por línea** y
procesa todas.

> este readme se irá completando en cada incremento. ahora mismo (incremento 1)
> solo está la estructura del proyecto y la lectura del archivo de entrada.

## requisitos

- **python 3.10 o superior**. no se usa ninguna librería externa (todo con la
  biblioteca estándar).

## ejecución

```bash
python main.py expresiones.txt
python main.py expresiones.txt -w babbaaaa -w abb
```

- el archivo tiene una expresión regular por línea.
- las líneas vacías y las que empiezan con `#` se ignoran.
- la cadena `w` se pasa con `-w` (se puede repetir) o, más adelante, se pedirá
  por teclado si no se indica.

## representación de epsilon

- en el **archivo de entrada** epsilon se escribe con la letra griega `ε`
  (u+03b5). se eligió porque es la notación matemática estándar y es muy
  improbable que forme parte del alfabeto de un lenguaje de prueba.
- **internamente** epsilon es un objeto único con su propio tipo (`EPSILON` en
  `src/simbolos.py`), no un carácter. así ninguna letra del alfabeto —ni el
  carácter nulo `\0`, ni un espacio, ni un metacarácter escapado— puede
  confundirse con él, y tampoco se confunde con `None` («aquí no hay
  transición»).

## caracteres especiales

solo 7 caracteres tienen significado especial dentro de una expresión:
`(` `)` `|` `*` `+` `\`… y `?`. cualquier otro carácter es un símbolo normal del
alfabeto. para usar uno de esos 7 como símbolo normal se escribe `\` delante
(por ejemplo `\*` es el asterisco como letra). `\0` es el carácter nulo.

## pruebas

```bash
python -m unittest discover -s tests -t tests
```

## estructura

```
Proyecto1TCC/
├── main.py                 lee el archivo de expresiones y (más adelante) corre todo
├── src/
│   ├── simbolos.py         ε, metacaracteres, escapes
│   └── errores.py          tipos de error reportables
├── tests/                  pruebas con unittest (biblioteca estándar)
├── expresiones.txt         archivo de ejemplo
└── Proyecto_1-1.pdf        enunciado
```
