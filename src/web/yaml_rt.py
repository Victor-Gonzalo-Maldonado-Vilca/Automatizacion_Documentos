"""Guardado de YAML conservando comentarios, orden y formato (ruamel.yaml).

La interfaz trabaja con valores de texto (como datos.leer_yaml). Al guardar,
solo se reemplazan los valores que cambiaron; el resto del archivo (comentarios,
comillas, "06", "23:59"...) queda igual.
"""

from __future__ import annotations

import io
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq


def _yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def _nuevo(valor):
    """Convierte un valor de la interfaz (texto, listas, dicts) para ruamel."""
    if isinstance(valor, dict):
        m = CommentedMap()
        for k, v in valor.items():
            m[k] = _nuevo(v)
        return m
    if isinstance(valor, list):
        return CommentedSeq([_nuevo(v) for v in valor])
    if valor in ("", None):
        return None
    if valor in ("true", "false"):
        return valor == "true"
    return valor


def _fusionar(nodo, original, nuevo):
    """Aplica `nuevo` sobre `nodo` (ruamel) usando `original` (texto) para detectar cambios."""
    if isinstance(nuevo, dict):
        if not isinstance(nodo, CommentedMap):
            return _nuevo(nuevo)
        orig = original if isinstance(original, dict) else {}
        for k in [k for k in nodo if k not in nuevo]:
            del nodo[k]
        for k, v in nuevo.items():
            if k in nodo:
                nodo[k] = _fusionar(nodo[k], orig.get(k), v)
            else:
                nodo[k] = _nuevo(v)
        return nodo
    if isinstance(nuevo, list):
        if not isinstance(nodo, CommentedSeq):
            return _nuevo(nuevo)
        orig = original if isinstance(original, list) else []
        for i, v in enumerate(nuevo):
            if i < len(nodo):
                nodo[i] = _fusionar(nodo[i], orig[i] if i < len(orig) else None, v)
            else:
                nodo.append(_nuevo(v))
        del nodo[len(nuevo):]
        return nodo
    # Escalar: si no cambió, se conserva el nodo original tal cual.
    if (original if original is not None else "") == (nuevo if nuevo is not None else ""):
        return nodo
    return _nuevo(nuevo)


def guardar(ruta: Path, original: dict, nuevo: dict) -> str:
    """Guarda `nuevo` en `ruta` conservando el formato. Devuelve el texto guardado."""
    y = _yaml()
    texto = ruta.read_text(encoding="utf-8")
    doc = y.load(texto) or CommentedMap()
    doc = _fusionar(doc, original, nuevo)
    salida = io.StringIO()
    y.dump(doc, salida)
    ruta.write_text(salida.getvalue(), encoding="utf-8")
    return salida.getvalue()
