"""Formato: informe de laboratorio (GUIA-PRLE-001) en PDF (Typst) y Word (.docx)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from datos import CONFIG_INSTITUCION, RAIZ, ErrorDatos, combinar, leer_yaml, slug

NOMBRE = "informe-laboratorio"
DESCRIPCION = "Informe de laboratorio (formato GUIA-PRLE-001)"
ARCHIVO = "informe.yaml"
SALIDAS = ("pdf", "docx")
PLANTILLAS = RAIZ / "plantillas" / "informe-laboratorio"
PLANTILLA_NUEVO = PLANTILLAS / "nuevo"
CARPETA_BUILD = RAIZ / ".build"


def _typst() -> str:
    exe = shutil.which("typst")
    if exe is None:
        raise ErrorDatos("No se encontró Typst. Instálalo con: winget install --id Typst.Typst")
    return exe


def cargar(ruta_yaml: Path) -> dict:
    """Datos del informe combinados con la configuración institucional."""
    datos = combinar(leer_yaml(CONFIG_INSTITUCION), leer_yaml(ruta_yaml))
    datos["dir"] = "/" + ruta_yaml.parent.resolve().relative_to(RAIZ).as_posix()
    return datos


def nombre_base(datos: dict, ruta_yaml: Path) -> str:
    archivo = datos.get("documento", {}).get("archivo", "")
    if archivo:
        return re.sub(r"\.(pdf|docx)$", "", archivo)
    titulo = datos.get("informacion", {}).get("titulo", "") or ruta_yaml.parent.name
    return f"Informe_{slug(titulo)}"


def generar_pdf(datos: dict, ruta_yaml: Path, pdf: Path) -> Path:
    CARPETA_BUILD.mkdir(exist_ok=True)
    ruta_json = CARPETA_BUILD / f"{ruta_yaml.parent.name}-{ruta_yaml.stem}.json"
    ruta_json.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    comando = [
        _typst(), "compile",
        "--root", str(RAIZ),
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
            from .informe_docx import generar_docx
            archivos.append(generar_docx(datos, ruta_yaml.parent, destino))
    return archivos
