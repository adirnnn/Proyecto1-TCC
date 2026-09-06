"""tipos de error del proyecto.

todos los errores "previsibles" (una expresión mal escrita, un archivo que no
existe, etc.) heredan de ``ErrorProyecto``. así el programa puede atrapar uno,
reportarlo y seguir con la siguiente línea del archivo sin abortar todo.
"""


class ErrorProyecto(Exception):
    """error base: cualquier problema previsible y reportable al usuario."""


class ErrorRegex(ErrorProyecto):
    """error al analizar o convertir una expresión regular."""


class ErrorExpresionVacia(ErrorRegex):
    """la línea no tiene ningún símbolo (está vacía o solo tiene espacios)."""


class ErrorParentesis(ErrorRegex):
    """paréntesis que no cierran, o un grupo vacío ``()``."""


class ErrorOperador(ErrorRegex):
    """un operador mal puesto: por ejemplo ``*`` sin nada a la izquierda."""


class ErrorSimbolo(ErrorRegex):
    """uso incorrecto de un carácter especial (por ejemplo ``\\`` al final)."""


class ErrorArchivo(ErrorProyecto):
    """no se pudo leer el archivo de expresiones."""
