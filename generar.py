"""Generador de documentos académicos.

Cada documento es un archivo YAML que declara su formato (`formato: ...`).
Una carpeta puede tener uno o varios documentos, independientes entre sí.

Uso:
    python generar.py documentos/lab07/informe.yaml        # un documento (todas sus salidas)
    python generar.py documentos/lab07 --salida docx       # solo el Word
    python generar.py documentos/lab07 --salida pdf,docx   # PDF y Word juntos
    python generar.py documentos/charla --salida pdf       # presentación solo en PDF
    python generar.py documentos/lab07                     # todos los de la carpeta
    python generar.py documentos/lab07 --formato presentacion
    python generar.py documentos/charla --tema azul
    python generar.py --todos                              # todo documentos/
    python generar.py --nuevo informe-laboratorio documentos/lab07
    python generar.py --nuevo presentacion documentos/charla
    python generar.py --formatos                           # formatos disponibles
    python generar.py --temas                              # temas de diapositivas
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from datos import RAIZ, ErrorDatos  # noqa: E402
from formatos import FORMATOS, crear_documento, documentos_en, elegir_salidas, formato_de  # noqa: E402

CARPETA_DOCUMENTOS = RAIZ / "documentos"
CARPETA_SALIDA = RAIZ / "output"


def objetivos(ruta: Path, solo: str | None) -> list[tuple[Path, object]]:
    """Documentos a generar a partir de un archivo YAML o una carpeta."""
    if ruta.is_file():
        modulo = formato_de(ruta)
        if modulo is None:
            raise ErrorDatos(f"{ruta.name} no declara `formato:` ({', '.join(FORMATOS)})")
        docs = [(ruta, modulo)]
    elif ruta.is_dir():
        docs = documentos_en(ruta)
        if not docs:
            raise ErrorDatos(f"No hay documentos (YAML con `formato:`) en {ruta}")
    else:
        raise ErrorDatos(f"No existe: {ruta}")
    if solo:
        docs = [(r, m) for r, m in docs if m.NOMBRE == solo]
        if not docs:
            raise ErrorDatos(f"No hay documentos de formato '{solo}' en {ruta}")
    return docs


def generar(docs, opciones: dict, abrir: bool, varios: bool = False) -> None:
    for ruta, modulo in docs:
        salida = CARPETA_SALIDA / ruta.parent.name
        pedidas = opciones.get("pedidas")
        if pedidas and (varios or len(docs) > 1):
            # En una carpeta con varios documentos, cada uno genera solo las
            # salidas pedidas que puede producir (los demás se omiten).
            pedidas = [x for x in pedidas if x.strip().lower().lstrip(".") in modulo.SALIDAS]
            if not pedidas:
                print(f"  [{modulo.NOMBRE}] {ruta.relative_to(RAIZ).as_posix()}  (omitido: no produce {opciones['pedidas']})")
                continue
        salidas = elegir_salidas(modulo, ruta, pedidas)
        archivos = modulo.generar(ruta, salida, {**opciones, "salidas": salidas})
        print(f"  [{modulo.NOMBRE}] {ruta.relative_to(RAIZ).as_posix()}")
        for archivo in archivos:
            print(f"      -> {archivo.relative_to(RAIZ).as_posix()}")
            if abrir:
                os.startfile(archivo)  # type: ignore[attr-defined]


def nuevo(formato: str, carpeta: Path) -> None:
    ruta = crear_documento(formato, carpeta)
    print(f"Creado {ruta.relative_to(RAIZ).as_posix()} ({FORMATOS[formato].DESCRIPCION}).")


def listar_formatos() -> None:
    print("Formatos disponibles:")
    for nombre, m in FORMATOS.items():
        print(f"  {nombre:<22} {m.DESCRIPCION}")
        print(f"  {'':<22} archivo: {m.ARCHIVO}   salidas: {', '.join(m.SALIDAS)}")


def main() -> int:
    p = argparse.ArgumentParser(description="Genera documentos académicos (PDF, PPTX, ...).")
    p.add_argument("ruta", nargs="?", help="archivo YAML de un documento o carpeta con documentos")
    p.add_argument("--formato", help="generar solo los documentos de este formato")
    p.add_argument("--salida", help="salidas separadas por coma: pdf, docx, pptx (por defecto, todas)")
    p.add_argument("--tema", help="tema de colores para presentaciones (ver --temas)")
    p.add_argument("--todos", action="store_true", help="generar todo lo que hay en documentos/")
    p.add_argument("--nuevo", nargs=2, metavar=("FORMATO", "CARPETA"), help="crear un documento desde su plantilla")
    p.add_argument("--formatos", action="store_true", help="listar formatos disponibles")
    p.add_argument("--temas", action="store_true", help="listar temas de presentación")
    p.add_argument("--abrir", action="store_true", help="abrir los archivos al terminar")
    a = p.parse_args()
    opciones = {"tema": a.tema, "pedidas": a.salida.split(",") if a.salida else None}

    try:
        if a.formatos:
            listar_formatos()
        elif a.temas:
            FORMATOS["presentacion"].listar_temas()
        elif a.nuevo:
            nuevo(a.nuevo[0], Path(a.nuevo[1]).resolve())
        elif a.todos:
            # Un documento con error no detiene a los demás.
            errores = []
            for carpeta in sorted(c for c in CARPETA_DOCUMENTOS.iterdir() if c.is_dir()):
                docs = documentos_en(carpeta)
                if a.formato:
                    docs = [(r, m) for r, m in docs if m.NOMBRE == a.formato]
                for doc in docs:
                    try:
                        generar([doc], opciones, a.abrir, varios=True)
                    except ErrorDatos as e:
                        errores.append(f"{doc[0].relative_to(RAIZ).as_posix()}: {e}")
            if errores:
                raise ErrorDatos(f"{len(errores)} documento(s) con errores:\n  " + "\n  ".join(errores))
        elif a.ruta:
            generar(objetivos(Path(a.ruta).resolve(), a.formato), opciones, a.abrir)
        else:
            p.print_help()
    except ErrorDatos as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main())
