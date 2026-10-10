"""Generación del informe PDF con Typst."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from datos import RAIZ, ErrorDatos, cargar_documento, slug

PLANTILLA = RAIZ / "plantillas" / "informe" / "main.typ"
CARPETA_BUILD = RAIZ / ".build"


def _typst() -> str:
    exe = shutil.which("typst")
    if exe is None:
        raise ErrorDatos("No se encontró Typst. Instálalo con: winget install --id Typst.Typst")
    return exe


def nombre_pdf(datos: dict, carpeta: Path) -> str:
    archivo = datos.get("documento", {}).get("archivo", "")
    if archivo:
        return archivo.removesuffix(".pdf") + ".pdf"
    titulo = datos.get("informacion", {}).get("titulo", "") or carpeta.name
    return f"Informe_{slug(titulo)}.pdf"


def generar_informe(carpeta: Path, salida: Path) -> Path:
    datos = cargar_documento(carpeta)

    CARPETA_BUILD.mkdir(exist_ok=True)
    ruta_json = CARPETA_BUILD / f"{carpeta.name}.json"
    ruta_json.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    salida.mkdir(parents=True, exist_ok=True)
    pdf = salida / nombre_pdf(datos, carpeta)
    comando = [
        _typst(), "compile",
        "--root", str(RAIZ),
        "--input", f"datos=/{ruta_json.relative_to(RAIZ).as_posix()}",
        "--font-path", str(RAIZ / "assets" / "fuentes"),
        str(PLANTILLA), str(pdf),
    ]
    proceso = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8")
    if proceso.returncode != 0:
        raise ErrorDatos("Typst no pudo compilar el informe:\n" + (proceso.stderr or proceso.stdout))
    if proceso.stderr.strip():
        print(proceso.stderr.strip())
    return pdf
