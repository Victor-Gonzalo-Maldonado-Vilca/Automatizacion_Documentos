"""Formato: informe académico con portada e índice, en PDF (Typst) y Word (.docx)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from datos import CONFIG_INSTITUCION, RAIZ, ErrorDatos, combinar, leer_yaml, slug

from .informe_laboratorio import CARPETA_BUILD, _typst

NOMBRE = "informe-academico"
DESCRIPCION = "Informe académico con portada e índice (Times New Roman)"
ARCHIVO = "informe.yaml"
SALIDAS = ("pdf", "docx")
PLANTILLAS = RAIZ / "plantillas" / "informe-academico"
PLANTILLA_NUEVO = PLANTILLAS / "nuevo"


def cargar(ruta_yaml: Path) -> dict:
    """Datos del documento + datos institucionales comunes (solo `institucion`)."""
    inst = leer_yaml(CONFIG_INSTITUCION).get("institucion", {})
    datos = combinar({"institucion": inst}, leer_yaml(ruta_yaml))
    datos["dir"] = "/" + ruta_yaml.parent.resolve().relative_to(RAIZ).as_posix()
    return datos


def nombre_base(datos: dict, ruta_yaml: Path) -> str:
    archivo = datos.get("archivo", "")
    if archivo:
        return re.sub(r"\.(pdf|docx)$", "", archivo)
    titulo = datos.get("portada", {}).get("titulo", "") or ruta_yaml.parent.name
    return f"Informe_{slug(titulo)}"


def generar_pdf(datos: dict, ruta_yaml: Path, pdf: Path) -> Path:
    import subprocess
    CARPETA_BUILD.mkdir(exist_ok=True)
    ruta_json = CARPETA_BUILD / f"{ruta_yaml.parent.name}-{ruta_yaml.stem}.json"
    ruta_json.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    comando = [
        _typst(), "compile", "--root", str(RAIZ),
        "--input", f"datos=/{ruta_json.relative_to(RAIZ).as_posix()}",
        "--font-path", str(RAIZ / "assets" / "fuentes"),
        str(PLANTILLAS / "main.typ"), str(pdf),
    ]
    proceso = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8")
    if proceso.returncode != 0:
        raise ErrorDatos("Typst no pudo compilar el informe:\n" + (proceso.stderr or proceso.stdout))
    if proceso.stderr.strip():
        print(proceso.stderr.strip())
    return pdf


def generar(ruta_yaml: Path, salida: Path, opciones: dict) -> list[Path]:
    datos = cargar(ruta_yaml)
    salida.mkdir(parents=True, exist_ok=True)
    base = nombre_base(datos, ruta_yaml)
    archivos = []
    for ext in opciones["salidas"]:
        destino = salida / f"{base}.{ext}"
        if ext == "pdf":
            archivos.append(generar_pdf(datos, ruta_yaml, destino))
        elif ext == "docx":
            from .informe_academico_docx import generar_docx
            archivos.append(generar_docx(datos, ruta_yaml.parent, destino))
    return archivos
