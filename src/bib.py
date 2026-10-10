"""Lector BibTeX mínimo y formato IEEE para la diapositiva de referencias.

El informe PDF no usa este módulo: Typst formatea las referencias por sí mismo.
"""

from __future__ import annotations

import re
from pathlib import Path

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_ABR = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.",
             "ago.", "sep.", "oct.", "nov.", "dic."]

_ACENTOS = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303"}


def _limpiar(valor: str) -> str:
    valor = re.sub(r"\\([%&_#$])", r"\1", valor)
    valor = re.sub(r"\\([`'^\"~])\{?(\w)\}?", lambda m: m.group(2) + _ACENTOS[m.group(1)], valor)
    valor = re.sub(r"\\\w+\s*", lambda m: m.group(0).strip("\\ "), valor)  # \TeX -> TeX
    valor = valor.replace("{", "").replace("}", "").replace("--", "–")
    import unicodedata
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", valor).strip())


def _valor(texto: str, i: int) -> tuple[str, int]:
    """Lee un valor {..} con llaves anidadas, "..." o un número desde i."""
    if texto[i] == "{":
        nivel, j = 0, i
        while j < len(texto):
            if texto[j] == "{":
                nivel += 1
            elif texto[j] == "}":
                nivel -= 1
                if nivel == 0:
                    return texto[i + 1:j], j + 1
            j += 1
        raise ValueError("Llaves sin cerrar en el .bib")
    if texto[i] == '"':
        j = texto.index('"', i + 1)
        return texto[i + 1:j], j + 1
    m = re.match(r"[\w.-]+", texto[i:])
    return (m.group(0), i + m.end()) if m else ("", i)


def leer_bib(ruta: Path) -> list[dict]:
    texto = re.sub(r"(?m)^\s*%.*$", "", ruta.read_text(encoding="utf-8"))
    entradas = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", texto):
        tipo, clave = m.group(1).lower(), m.group(2)
        if tipo in ("comment", "preamble", "string"):
            continue
        campos, i = {}, m.end()
        while i < len(texto):
            c = re.match(r"\s*(\w+)\s*=\s*", texto[i:])
            if not c:
                break
            i += c.end()
            valor, i = _valor(texto, i)
            corporativo = valor.startswith("{") and valor.endswith("}")
            campos[c.group(1).lower()] = (valor, corporativo)
            fin = re.match(r"\s*,?", texto[i:])
            i += fin.end()
            if texto[i:].lstrip().startswith("}"):
                break
        entradas.append({"tipo": tipo, "clave": clave, "campos": campos})
    return entradas


def _autor(nombre: str) -> str:
    """'Knuth, Donald E.' o 'Donald E. Knuth' -> 'D. E. Knuth'."""
    nombre = _limpiar(nombre)
    if "," in nombre:
        apellido, nombres = [p.strip() for p in nombre.split(",", 1)]
    else:
        partes = nombre.split()
        apellido, nombres = partes[-1], " ".join(partes[:-1])
    iniciales = " ".join(p[0] + "." for p in re.split(r"[\s]+", nombres) if p)
    return f"{iniciales} {apellido}".strip()


def _autores(campo: tuple[str, bool] | None) -> str:
    if not campo:
        return ""
    valor, corporativo = campo
    if corporativo:
        return _limpiar(valor)
    nombres = [_autor(n) for n in re.split(r"\s+and\s+", valor)]
    if len(nombres) > 6:
        return nombres[0] + " et al."
    if len(nombres) <= 2:
        return " y ".join(nombres)
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def _fecha(iso: str) -> str:
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", iso)
    if not m:
        return iso
    return f"{int(m.group(3))} de {MESES[int(m.group(2)) - 1]} de {m.group(1)}"


def formato_ieee(e: dict) -> list[tuple[str, bool]]:
    """Devuelve la referencia como segmentos (texto, cursiva)."""
    f = {k: _limpiar(v[0]) for k, v in e["campos"].items()}
    autores = _autores(e["campos"].get("author") or e["campos"].get("editor"))
    titulo, anio = f.get("title", ""), f.get("year", "")
    mes = f.get("month", "")
    if mes.isdigit():
        mes = MESES_ABR[int(mes) - 1]
    lugar_ed = ", ".join(x for x in (f.get("address"), f.get("publisher") or f.get("organization")) if x)
    pre = f"{autores}, " if autores else ""
    s: list[tuple[str, bool]] = []
    tipo = e["tipo"]

    if tipo == "article":
        s += [(f"{pre}“{titulo},” ", False), (f.get("journal", ""), True)]
        resto = [f"vol. {f['volume']}" if "volume" in f else "", f"no. {f['number']}" if "number" in f else "",
                 f"pp. {f['pages']}" if "pages" in f else "", " ".join(x for x in (mes, anio) if x)]
        s.append((", " + ", ".join(x for x in resto if x) + ".", False))
    elif tipo == "book":
        s += [(pre, False), (titulo, True)]
        ed = f", {f['edition']} ed" if "edition" in f else ""
        lugar = f.get("address", "")
        editorial = f.get("publisher", "")
        s.append((f"{ed}. {lugar + ': ' if lugar else ''}{editorial}{', ' if editorial else ''}{anio}.", False))
    elif tipo in ("inproceedings", "conference", "incollection"):
        s += [(f"{pre}“{titulo},” en ", False), (f.get("booktitle", ""), True)]
        resto = [f.get("address", ""), " ".join(x for x in (mes, anio) if x), f"pp. {f['pages']}" if "pages" in f else ""]
        s.append((", " + ", ".join(x for x in resto if x) + ".", False))
    elif "url" in f:
        s.append((f"{pre}“{titulo}.” ", False))
        if f.get("organization") or f.get("howpublished"):
            s.append((f"{f.get('organization') or f.get('howpublished')}. ", False))
        if f.get("urldate"):
            s.append((f"Accedido: {_fecha(f['urldate'])}. ", False))
        s.append((f"[En línea]. Disponible en: {f['url']}", False))
    else:  # manual, techreport, misc, thesis...
        s.append((f"{pre}“{titulo},” ", False))
        if tipo in ("phdthesis", "mastersthesis"):
            s.append(("Tesis doctoral, " if tipo == "phdthesis" else "Tesis de maestría, ", False))
            lugar_ed = ", ".join(x for x in (f.get("school"), f.get("address")) if x)
        s.append((", ".join(x for x in (lugar_ed, anio) if x) + ".", False))
    return [(t, c) for t, c in s if t]
