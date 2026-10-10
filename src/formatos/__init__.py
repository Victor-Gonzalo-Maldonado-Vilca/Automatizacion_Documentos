"""Registro de formatos de documento.

Cada formato es un módulo independiente que define:

    NOMBRE           identificador usado en `formato:` del YAML y en la CLI
    DESCRIPCION      texto corto para `--formatos`
    ARCHIVO          nombre por defecto del YAML (ej. "informe.yaml")
    PLANTILLA_NUEVO  carpeta que copia `--nuevo`
    SALIDAS          extensiones que puede producir, la principal primero
    generar(ruta_yaml, salida, opciones) -> list[Path]
                     opciones["salidas"]: lista elegida (ver elegir_salidas)

Para agregar un formato nuevo: crear el módulo en esta carpeta y añadirlo
a la tupla de abajo.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from datos import ErrorDatos, leer_yaml

from . import informe_academico, informe_laboratorio, presentacion

FORMATOS = {m.NOMBRE: m for m in (informe_laboratorio, informe_academico, presentacion)}


def formato_de(ruta_yaml: Path):
    """Módulo del formato declarado en un YAML (o deducido por su nombre)."""
    nombre = leer_yaml(ruta_yaml).get("formato", "")
    if not nombre:
        nombre = next((n for n, m in FORMATOS.items() if m.ARCHIVO == ruta_yaml.name), "")
    if not nombre:
        return None
    if nombre not in FORMATOS:
        raise ErrorDatos(f"{ruta_yaml.name}: formato '{nombre}' desconocido. "
                         f"Disponibles: {', '.join(FORMATOS)}")
    return FORMATOS[nombre]


def documentos_en(carpeta: Path) -> list[tuple[Path, object]]:
    """Todos los YAML de una carpeta que declaran un formato conocido."""
    encontrados = []
    for ruta in sorted(carpeta.glob("*.yaml")):
        modulo = formato_de(ruta)
        if modulo is not None:
            encontrados.append((ruta, modulo))
    return encontrados


def elegir_salidas(modulo, ruta_yaml: Path, pedidas: list[str] | None) -> list[str]:
    """Salidas a generar: las pedidas en la CLI, o `salidas:` del YAML, o todas."""
    if pedidas:
        lista = pedidas
    else:
        del_yaml = leer_yaml(ruta_yaml).get("salidas")
        lista = del_yaml if isinstance(del_yaml, list) else ([del_yaml] if del_yaml else list(modulo.SALIDAS))
    lista = [s.strip().lower().lstrip(".") for s in lista if s and s.strip()]
    invalidas = [s for s in lista if s not in modulo.SALIDAS]
    if invalidas:
        raise ErrorDatos(f"{ruta_yaml.name}: el formato '{modulo.NOMBRE}' no produce {', '.join(invalidas)}. "
                         f"Salidas posibles: {', '.join(modulo.SALIDAS)}")
    return lista


def crear_documento(formato: str, carpeta: Path) -> Path:
    """Copia el esqueleto de un formato en `carpeta` sin pisar archivos existentes.

    Permite sumar un formato a una carpeta que ya tiene otro documento.
    Devuelve la ruta del YAML creado.
    """
    if formato not in FORMATOS:
        raise ErrorDatos(f"Formato '{formato}' desconocido. Disponibles: {', '.join(FORMATOS)}")
    modulo = FORMATOS[formato]
    if (carpeta / modulo.ARCHIVO).exists():
        raise ErrorDatos(f"Ya existe {carpeta.name}/{modulo.ARCHIVO}")
    for origen in modulo.PLANTILLA_NUEVO.rglob("*"):
        destino = carpeta / origen.relative_to(modulo.PLANTILLA_NUEVO)
        if origen.is_dir():
            destino.mkdir(parents=True, exist_ok=True)
        elif not destino.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origen, destino)
    return carpeta / modulo.ARCHIVO
