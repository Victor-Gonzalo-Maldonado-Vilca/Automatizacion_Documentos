"""Carga y combinación de los archivos YAML del proyecto."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
CONFIG_INSTITUCION = RAIZ / "config" / "institucion.yaml"


class ErrorDatos(Exception):
    """Error de contenido en un archivo YAML del usuario."""


def _normalizar(valor):
    """BaseLoader devuelve todo como texto; convierte 'null'/'~' en vacío."""
    if isinstance(valor, dict):
        return {str(k): _normalizar(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_normalizar(v) for v in valor]
    if valor is None or valor in ("~", "null", "Null", "NULL"):
        return ""
    return valor


def leer_yaml(ruta: Path) -> dict:
    """Lee un YAML tratando todos los valores como texto.

    Así "06" no se convierte en 6 ni "23:59" en un número sexagesimal.
    """
    if not ruta.exists():
        raise ErrorDatos(f"No existe el archivo: {ruta}")
    try:
        with ruta.open(encoding="utf-8") as f:
            contenido = yaml.load(f, Loader=yaml.BaseLoader)
    except yaml.YAMLError as e:
        raise ErrorDatos(f"Error de formato en {ruta.name}:\n{e}") from e
    return _normalizar(contenido or {})


def combinar(base: dict, extra: dict) -> dict:
    """Combina diccionarios recursivamente; `extra` tiene prioridad."""
    resultado = dict(base)
    for clave, valor in extra.items():
        if isinstance(valor, dict) and isinstance(resultado.get(clave), dict):
            resultado[clave] = combinar(resultado[clave], valor)
        else:
            resultado[clave] = valor
    return resultado


def cargar_documento(carpeta: Path) -> dict:
    """Datos del documento ya combinados con la configuración institucional."""
    datos = combinar(leer_yaml(CONFIG_INSTITUCION), leer_yaml(carpeta / "datos.yaml"))
    datos["dir"] = "/" + carpeta.resolve().relative_to(RAIZ).as_posix()
    return datos


def a_lista(valor) -> list:
    if valor in (None, ""):
        return []
    return valor if isinstance(valor, list) else [valor]


def slug(texto: str) -> str:
    """'Título de la Práctica' -> 'Titulo_de_la_Practica'."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto).strip()
    return re.sub(r"[\s-]+", "_", texto)[:60] or "documento"
