"""Resaltado de sintaxis común (Pygments) para Word y PowerPoint."""

from __future__ import annotations

# (prefijo de token, color, cursiva). Se usa el primer prefijo que coincide.
OSCURO = [  # fondo oscuro, estilo "Dark+" (diapositivas)
    ("Comment", "#6A9955", True),
    ("Keyword.Type", "#4EC9B0", False),
    ("Keyword", "#569CD6", False),
    ("Name.Class", "#4EC9B0", False),
    ("Name.Function", "#DCDCAA", False),
    ("Name.Decorator", "#DCDCAA", False),
    ("Name.Builtin", "#4EC9B0", False),
    ("Name.Attribute", "#9CDCFE", False),
    ("Literal.String", "#CE9178", False),
    ("Literal.Number", "#B5CEA8", False),
]
OSCURO_TEXTO = "#D4D4D4"

CLARO = [  # fondo claro, similar al del informe PDF (Typst)
    ("Comment", "#8A8A8A", True),
    ("Keyword", "#D73A49", False),
    ("Name.Class", "#6F42C1", False),
    ("Name.Function", "#4B69C6", False),
    ("Name.Decorator", "#4B69C6", False),
    ("Name.Builtin", "#4B69C6", False),
    ("Literal.String", "#298E0D", False),
    ("Literal.Number", "#B60157", False),
    ("Operator", "#D73A49", False),
]
CLARO_TEXTO = "#1F1F1F"


def resaltar(codigo: str, lenguaje: str = "", nombre: str = "", paleta=OSCURO,
             texto: str = OSCURO_TEXTO) -> list[list[tuple[str, str, bool]]]:
    """Divide el código en líneas de segmentos (texto, color, cursiva)."""
    lexer = None
    try:
        from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
        from pygments.util import ClassNotFound
        try:
            lexer = get_lexer_by_name(lenguaje) if lenguaje else get_lexer_for_filename(nombre or "x.txt")
        except ClassNotFound:
            lexer = None
    except ImportError:
        pass
    if lexer is None:
        return [[(l, texto, False)] for l in codigo.splitlines()]

    lineas: list[list[tuple[str, str, bool]]] = [[]]
    for tipo, valor in lexer.get_tokens(codigo):
        nombre_tipo = str(tipo).removeprefix("Token.")
        color, cursiva = texto, False
        for prefijo, c, it in paleta:
            if nombre_tipo.startswith(prefijo):
                color, cursiva = c, it
                break
        for k, parte in enumerate(valor.split("\n")):
            if k > 0:
                lineas.append([])
            if parte:
                lineas[-1].append((parte, color, cursiva))
    while lineas and not lineas[-1]:
        lineas.pop()
    return lineas
