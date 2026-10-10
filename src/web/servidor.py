"""Servidor de la interfaz gráfica (Flask, solo para uso local).

Expone una API JSON sobre la misma lógica que usa generar.py: listar y crear
documentos, editar sus datos y archivos, subir imágenes y generar las salidas.
Todas las rutas de archivos se limitan a documentos/ y output/.
"""

from __future__ import annotations

import contextlib
import io
import os
import re
import threading
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

from datos import RAIZ, ErrorDatos, leer_yaml
from formatos import FORMATOS, crear_documento, documentos_en, elegir_salidas, formato_de

from . import yaml_rt

DOCUMENTOS = RAIZ / "documentos"
SALIDA = RAIZ / "output"
ESTATICOS = Path(__file__).parent / "static"

TEXTO = {".typ", ".bib", ".yaml", ".yml", ".txt", ".md", ".py", ".cs", ".js", ".ts", ".java", ".c",
         ".cpp", ".h", ".html", ".css", ".sql", ".json", ".sh", ".ps1", ".go", ".rs", ".php", ".kt"}
IMAGENES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}

_generando = threading.Lock()


def _dentro(base: Path, relativa: str) -> Path:
    """Resuelve una ruta relativa a la raíz y verifica que quede dentro de `base`."""
    ruta = (RAIZ / relativa).resolve()
    if base.resolve() not in ruta.parents and ruta != base.resolve():
        abort(403, "Ruta no permitida")
    return ruta


def _rel(ruta: Path) -> str:
    return ruta.resolve().relative_to(RAIZ).as_posix()


def _error(mensaje: str, codigo: int = 400):
    return jsonify({"error": mensaje}), codigo


def _titulo(datos: dict, carpeta: str) -> str:
    for camino in (("informacion", "titulo"), ("portada", "titulo"), ("datos", "titulo")):
        v = datos
        for k in camino:
            v = v.get(k, {}) if isinstance(v, dict) else {}
        if isinstance(v, str) and v:
            return v
    return carpeta


def _archivos(carpeta: Path) -> dict:
    todos = [p for p in carpeta.rglob("*") if p.is_file() and ".git" not in p.parts]
    rel = lambda p: p.relative_to(carpeta).as_posix()  # noqa: E731
    return {
        "contenido": sorted(rel(p) for p in todos if p.suffix == ".typ"),
        "imagenes": sorted(rel(p) for p in todos if p.suffix.lower() in IMAGENES),
        "codigo": sorted(rel(p) for p in todos if p.suffix in TEXTO - {".typ", ".bib", ".yaml", ".yml"}),
        "bib": sorted(rel(p) for p in todos if p.suffix == ".bib"),
    }


def _salidas_de(ruta_yaml: Path, modulo) -> list[dict]:
    """Archivos ya generados para este documento (en output/<carpeta>/)."""
    carpeta = SALIDA / ruta_yaml.parent.name
    if not carpeta.exists():
        return []
    extensiones = {"." + s for s in modulo.SALIDAS}
    archivos = sorted((p for p in carpeta.iterdir() if p.suffix in extensiones), key=lambda p: -p.stat().st_mtime)
    return [{"ruta": _rel(p), "nombre": p.name, "ext": p.suffix[1:]} for p in archivos]


def crear_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.json.ensure_ascii = False
    app.json.sort_keys = False  # el formulario respeta el orden del YAML

    @app.errorhandler(ErrorDatos)
    def _err_datos(e):
        return _error(str(e))

    @app.errorhandler(403)
    def _err_403(e):
        return _error(getattr(e, "description", "Prohibido"), 403)

    # --- páginas --------------------------------------------------------------
    @app.get("/")
    def inicio():
        return send_from_directory(ESTATICOS, "index.html")

    @app.get("/static/<path:archivo>")
    def estaticos(archivo):
        return send_from_directory(ESTATICOS, archivo)

    @app.get("/archivos/<path:ruta>")
    def archivos(ruta):
        p = (RAIZ / ruta).resolve()
        if not any(base.resolve() in p.parents for base in (DOCUMENTOS, SALIDA)):
            abort(403, "Ruta no permitida")
        if not p.is_file():
            abort(404)
        descargar = request.args.get("descargar") == "1"
        return send_from_directory(p.parent, p.name, as_attachment=descargar, max_age=0)

    # --- información general ------------------------------------------------------
    @app.get("/api/estado")
    def estado():
        from formatos import presentacion
        temas = leer_yaml(presentacion.TEMAS)
        temas.pop("_fuentes", None)
        return jsonify({
            "formatos": [{"nombre": n, "descripcion": m.DESCRIPCION, "salidas": list(m.SALIDAS),
                          "archivo": m.ARCHIVO} for n, m in FORMATOS.items()],
            "temas": [{"clave": k, "nombre": v.get("nombre", k), "primario": v.get("primario", "")}
                      for k, v in temas.items()],
            "tipos_diapositiva": presentacion.TIPOS,
        })

    @app.get("/api/documentos")
    def documentos():
        lista = []
        for carpeta in sorted(c for c in DOCUMENTOS.iterdir() if c.is_dir()):
            for ruta, modulo in documentos_en(carpeta):
                datos = leer_yaml(ruta)
                lista.append({"ruta": _rel(ruta), "carpeta": carpeta.name, "archivo": ruta.name,
                              "formato": modulo.NOMBRE, "titulo": _titulo(datos, carpeta.name)})
        return jsonify(lista)

    @app.post("/api/nuevo")
    def nuevo():
        cuerpo = request.get_json(force=True)
        nombre = re.sub(r"[^\w\-]+", "_", (cuerpo.get("carpeta") or "").strip()).strip("_")
        if not nombre:
            return _error("Escribe un nombre para la carpeta")
        ruta = crear_documento(cuerpo.get("formato", ""), DOCUMENTOS / nombre)
        return jsonify({"ruta": _rel(ruta)})

    # --- documento ---------------------------------------------------------------------
    @app.get("/api/documento")
    def documento():
        ruta = _dentro(DOCUMENTOS, request.args.get("ruta", ""))
        modulo = formato_de(ruta)
        if modulo is None:
            return _error("El archivo no declara un formato")
        return jsonify({
            "ruta": _rel(ruta), "carpeta": _rel(ruta.parent), "formato": modulo.NOMBRE,
            "salidas_posibles": list(modulo.SALIDAS),
            "salidas_defecto": elegir_salidas(modulo, ruta, None),
            "yaml": ruta.read_text(encoding="utf-8"),
            "datos": leer_yaml(ruta),
            "archivos": _archivos(ruta.parent),
            "generados": _salidas_de(ruta, modulo),
        })

    @app.post("/api/documento")
    def guardar_documento():
        cuerpo = request.get_json(force=True)
        ruta = _dentro(DOCUMENTOS, cuerpo.get("ruta", ""))
        if "yaml" in cuerpo:  # edición directa del YAML
            texto = cuerpo["yaml"]
            tmp = ruta.with_suffix(".tmp")
            tmp.write_text(texto, encoding="utf-8")
            try:
                leer_yaml(tmp)
            finally:
                tmp.unlink(missing_ok=True)
            ruta.write_text(texto, encoding="utf-8")
        else:
            texto = yaml_rt.guardar(ruta, leer_yaml(ruta), cuerpo.get("datos", {}))
        return jsonify({"yaml": texto, "datos": leer_yaml(ruta)})

    # --- archivos de texto e imágenes ---------------------------------------------------
    @app.get("/api/archivo")
    def leer_archivo():
        ruta = _dentro(DOCUMENTOS, request.args.get("ruta", ""))
        if ruta.suffix not in TEXTO:
            return _error("Solo se pueden editar archivos de texto")
        if not ruta.exists():
            return _error("El archivo no existe", 404)
        return jsonify({"ruta": _rel(ruta), "texto": ruta.read_text(encoding="utf-8")})

    @app.post("/api/archivo")
    def guardar_archivo():
        cuerpo = request.get_json(force=True)
        ruta = _dentro(DOCUMENTOS, cuerpo.get("ruta", ""))
        if ruta.suffix not in TEXTO:
            return _error("Solo se pueden guardar archivos de texto")
        if cuerpo.get("crear") and ruta.exists():
            return _error(f"Ya existe {ruta.name}")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(cuerpo.get("texto", ""), encoding="utf-8")
        return jsonify({"ruta": _rel(ruta)})

    @app.delete("/api/archivo")
    def borrar_archivo():
        ruta = _dentro(DOCUMENTOS, request.args.get("ruta", ""))
        if ruta.suffix in (".yaml", ".yml"):
            return _error("Los archivos de datos no se borran desde aquí")
        if ruta.is_file():
            ruta.unlink()
        return jsonify({"ok": True})

    @app.post("/api/subir")
    def subir():
        carpeta = _dentro(DOCUMENTOS, request.form.get("carpeta", ""))
        destino = carpeta / request.form.get("subcarpeta", "imagenes")
        destino = _dentro(DOCUMENTOS, _rel(destino))
        guardados = []
        for f in request.files.getlist("archivos"):
            nombre = re.sub(r"[^\w.\-]+", "_", Path(f.filename or "archivo").name)
            if Path(nombre).suffix.lower() not in IMAGENES | TEXTO:
                return _error(f"Tipo de archivo no permitido: {nombre}")
            destino.mkdir(parents=True, exist_ok=True)
            f.save(destino / nombre)
            guardados.append((destino / nombre).relative_to(carpeta).as_posix())
        return jsonify({"guardados": guardados})

    # --- generación ----------------------------------------------------------------------
    @app.post("/api/generar")
    def generar():
        cuerpo = request.get_json(force=True)
        ruta = _dentro(DOCUMENTOS, cuerpo.get("ruta", ""))
        modulo = formato_de(ruta)
        if modulo is None:
            return _error("El archivo no declara un formato")
        salidas = elegir_salidas(modulo, ruta, cuerpo.get("salidas") or None)
        registro = io.StringIO()
        with _generando, contextlib.redirect_stdout(registro):
            archivos = modulo.generar(ruta, SALIDA / ruta.parent.name,
                                      {"salidas": salidas, "tema": cuerpo.get("tema") or None})
        return jsonify({
            "archivos": [{"ruta": _rel(a), "nombre": a.name, "ext": a.suffix[1:]} for a in archivos],
            "registro": registro.getvalue(),
        })

    @app.post("/api/abrir")
    def abrir():
        cuerpo = request.get_json(force=True)
        p = (RAIZ / cuerpo.get("ruta", "")).resolve()
        if not any(base.resolve() in p.parents for base in (DOCUMENTOS, SALIDA)) or not p.exists():
            abort(403, "Ruta no permitida")
        if hasattr(os, "startfile"):
            os.startfile(p)  # type: ignore[attr-defined]
        return jsonify({"ok": True})

    return app
