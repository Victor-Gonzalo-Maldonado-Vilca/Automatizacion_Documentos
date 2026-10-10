"""Generador de documentos académicos (informe PDF + diapositivas PPTX).

Uso:
    python generar.py documentos/ejemplo            # informe y diapositivas
    python generar.py documentos/ejemplo --solo pdf
    python generar.py documentos/ejemplo --solo pptx --tema azul
    python generar.py --todos                       # todas las carpetas de documentos/
    python generar.py --nuevo documentos/lab07      # crea un documento desde cero
    python generar.py --temas                       # lista los temas de diapositivas
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from datos import RAIZ, ErrorDatos  # noqa: E402
from informe import generar_informe  # noqa: E402

CARPETA_DOCUMENTOS = RAIZ / "documentos"
CARPETA_SALIDA = RAIZ / "output"
PLANTILLA_NUEVO = RAIZ / "plantillas" / "nuevo"


def generar(carpeta: Path, solo: str | None, tema: str | None, abrir: bool) -> None:
    salida = CARPETA_SALIDA / carpeta.name
    print(f"\n== {carpeta.relative_to(RAIZ).as_posix()} ==")
    archivos = []
    if solo in (None, "pdf"):
        archivos.append(generar_informe(carpeta, salida))
        print(f"  Informe:       {archivos[-1].relative_to(RAIZ)}")
    if solo in (None, "pptx"):
        if (carpeta / "diapositivas.yaml").exists():
            from presentacion import generar_presentacion
            archivos.append(generar_presentacion(carpeta, salida, tema))
            print(f"  Diapositivas:  {archivos[-1].relative_to(RAIZ)}")
        elif solo == "pptx":
            raise ErrorDatos(f"{carpeta.name} no tiene diapositivas.yaml")
    if abrir:
        for a in archivos:
            os.startfile(a)  # type: ignore[attr-defined]


def nuevo(carpeta: Path) -> None:
    if carpeta.exists():
        raise ErrorDatos(f"Ya existe: {carpeta}")
    shutil.copytree(PLANTILLA_NUEVO, carpeta)
    print(f"Documento creado en {carpeta.relative_to(RAIZ)}. Edita datos.yaml y diapositivas.yaml.")


def main() -> int:
    p = argparse.ArgumentParser(description="Genera informes PDF y diapositivas PPTX.")
    p.add_argument("carpeta", nargs="?", help="carpeta del documento (ej. documentos/ejemplo)")
    p.add_argument("--solo", choices=["pdf", "pptx"], help="generar solo uno de los formatos")
    p.add_argument("--tema", help="tema de colores para las diapositivas (ver --temas)")
    p.add_argument("--todos", action="store_true", help="generar todos los documentos")
    p.add_argument("--nuevo", metavar="CARPETA", help="crear un documento nuevo desde la plantilla")
    p.add_argument("--temas", action="store_true", help="listar temas de diapositivas")
    p.add_argument("--abrir", action="store_true", help="abrir los archivos al terminar")
    a = p.parse_args()

    try:
        if a.temas:
            from presentacion import listar_temas
            listar_temas()
        elif a.nuevo:
            nuevo(Path(a.nuevo).resolve())
        elif a.todos:
            for c in sorted(CARPETA_DOCUMENTOS.iterdir()):
                if (c / "datos.yaml").exists():
                    generar(c, a.solo, a.tema, a.abrir)
        elif a.carpeta:
            carpeta = Path(a.carpeta).resolve()
            if not (carpeta / "datos.yaml").exists():
                raise ErrorDatos(f"No se encontró datos.yaml en {carpeta}")
            generar(carpeta, a.solo, a.tema, a.abrir)
        else:
            p.print_help()
    except ErrorDatos as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
