'''Formatos de carta de renuncia.'''

from __future__ import annotations
import json
import subprocess
from pathlib import Path
from datos import RAIZ, ErrorDatos, leer_yaml, slug

from .informe_laboratorio import CARPETA_BUILD, _typst

NOMBRE = "carta-renuncia"
DESCRIPCION = "Carta de renuncia laboral"
ARCHIVO = "carta.yaml"
SALIDAS = ["pdf",]
PLANTILLA = RAIZ / "plantillas" / "carta-renuncia"
PLANTILLA_NUEVO = PLANTILLA / "nuevo"

def nombre_base(datos:dict, ruta_yaml:Path) -> str:
    '''Devuelve el nombre base del archivo de salida.'''
    remitente = datos.get("remitente") or {}
    nombre = remitente.get("nombre", "").strip()
    identificador = nombre or ruta_yaml.parent.name
    identificador_limpio = slug(identificador)
    return f"Carta_Renuncia_{identificador_limpio}"

def generar(ruta_yaml:Path, salida:Path, opciones:dict) -> list[Path]:
    '''Genera la carta de renuncia en formato PDF.'''
    datos = cargar(ruta_yaml)
    salida.mkdir(parents=True, exist_ok=True)
    pdf = salida / f"{nombre_base(datos, ruta_yaml)}.pdf"

    CARPETA_BUILD.mkdir(parents=True, exist_ok=True)
    ruta_json = CARPETA_BUILD / f"{ruta_yaml.parent.name}-{ruta_yaml.stem}.json"
    ruta_json.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")

    comando = [
        _typst(),
        "compile",
        "--root", str(RAIZ),
        "--input", f"datos=/{ruta_json.relative_to(RAIZ).as_posix()}",
        str(PLANTILLA / "main.typ"), str(pdf),
    ]
    proceso = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8")
    if proceso.returncode != 0:
        raise ErrorDatos("Typst no pudo compilar la carta:\n" + proceso.stderr)
    return [pdf]

def cargar(ruta_yaml: Path) -> dict:
    """Lee el YAML de la carta."""
    datos = leer_yaml(ruta_yaml)
    datos["dir"] = "/" + ruta_yaml.parent.resolve().relative_to(RAIZ).as_posix()
    return datos