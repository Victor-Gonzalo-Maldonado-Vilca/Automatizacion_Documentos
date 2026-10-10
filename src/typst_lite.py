"""Lector del subconjunto de Typst usado en los archivos de contenido.

Convierte el texto en bloques simples para generar otros formatos (Word).
Soporta lo documentado en el README: títulos (=), párrafos, listas (- / +),
*negrita*, _cursiva_, `código`, citas @clave, referencias @fig:x, saltos (\\),
ecuaciones $...$, bloques ```código```, y los componentes #captura, #tabla,
#codigo, #nota (además de #image y #figure básicos).

Bloques:
  {"t": "titulo", "nivel": n, "inl": [...]}
  {"t": "parrafo", "inl": [...]}
  {"t": "lista", "items": [(nivel, ordenada, [...inl])]}
  {"t": "codigo", "codigo": str, "lenguaje": str, "titulo": str|None, "pie": [...]|None}
  {"t": "figura", "ruta": str, "ancho": float, "borde": bool, "pie": [...]|None}
  {"t": "tabla", "columnas": [...], "encabezado": [[inl]], "celdas": [[inl]], "pie": [...]|None}
  {"t": "nota", "titulo": [...], "inl": [...]}
  {"t": "ecuacion", "math": str}
  Todos pueden llevar "etiqueta" (<fig:x>).

Inline:
  {"txt": str, "b": bool, "i": bool, "code": bool}
  {"math": str}   {"cita": clave}   {"salto": True}
"""

from __future__ import annotations

import re

_RE_LLAMADA = re.compile(r"#([A-Za-z_][\w-]*)(?=[(\[])")
_RE_ETIQUETA = re.compile(r"[ \t]*<([\w:.\-]+)>")


# ============================================================================
#  Utilidades de escaneo
# ============================================================================

def _saltar_raw(src: str, p: int) -> int:
    """Desde un '`', devuelve la posición tras el bloque/inline raw."""
    n = len(src)
    q = p
    while q < n and src[q] == "`":
        q += 1
    marca = src[p:q]
    fin = src.find(marca, q)
    return n if fin == -1 else fin + len(marca)


def _balanceado(src: str, p: int) -> tuple[str, int]:
    """src[p] es '(' o '['. Devuelve (interior, posición tras el cierre)."""
    abre = src[p]
    cierra = ")" if abre == "(" else "]"
    nivel, q, n = 0, p, len(src)
    while q < n:
        c = src[q]
        if c == "\\":
            q += 2
            continue
        if c == "`":
            q = _saltar_raw(src, q)
            continue
        if c == '"' and abre == "(":
            q += 1
            while q < n and src[q] != '"':
                q += 2 if src[q] == "\\" else 1
        elif c in "([":
            nivel += 1
        elif c in ")]":
            nivel -= 1
            if nivel == 0:
                return src[p + 1:q], q + 1
        q += 1
    raise ValueError(f"Paréntesis o corchetes sin cerrar cerca de: {src[p:p + 40]!r}")


def _dividir_args(texto: str) -> list[str]:
    """Divide por comas de nivel superior."""
    partes, nivel, actual, q, n = [], 0, [], 0, len(texto)
    while q < n:
        c = texto[q]
        if c == "`":
            fin = _saltar_raw(texto, q)
            actual.append(texto[q:fin])
            q = fin
            continue
        if c == '"':
            r = q + 1
            while r < n and texto[r] != '"':
                r += 2 if texto[r] == "\\" else 1
            actual.append(texto[q:r + 1])
            q = r + 1
            continue
        if c in "([{":
            nivel += 1
        elif c in ")]}":
            nivel -= 1
        if c == "," and nivel == 0:
            partes.append("".join(actual))
            actual = []
        else:
            actual.append(c)
        q += 1
    if "".join(actual).strip():
        partes.append("".join(actual))
    return [p.strip() for p in partes if p.strip()]


def _valor(v: str):
    """Convierte un argumento Typst en un valor Python sencillo."""
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        return {"str": v[1:-1].replace('\\"', '"').replace("\\\\", "\\")}
    if v.startswith("[") and v.endswith("]"):
        return {"contenido": v[1:-1]}
    if v.startswith("(") and v.endswith(")"):
        return {"tupla": [_valor(x) for x in _dividir_args(v[1:-1])]}
    m = _RE_LLAMADA.match("#" + v) if not v.startswith("#") else _RE_LLAMADA.match(v)
    if m:
        llamada = _leer_llamada("#" + v.lstrip("#"), 0)
        return {"llamada": llamada[0], "args": llamada[1]}
    return {"raw": v}


def _leer_llamada(src: str, p: int):
    """src[p] == '#'. Devuelve ((nombre, posicionales, nombrados), fin)."""
    m = _RE_LLAMADA.match(src, p)
    nombre = m.group(1)
    q = m.end()
    pos, nom = [], {}
    if q < len(src) and src[q] == "(":
        interior, q = _balanceado(src, q)
        for arg in _dividir_args(interior):
            mn = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", arg, re.S)
            if mn and not arg.startswith(('"', "[")):
                nom[mn.group(1)] = _valor(mn.group(2))
            else:
                pos.append(_valor(arg))
    while q < len(src) and src[q] == "[":
        interior, q = _balanceado(src, q)
        pos.append({"contenido": interior})
    return (nombre, pos, nom), q


# ============================================================================
#  Inline
# ============================================================================

def _limite(texto: str, i: int, apertura: bool) -> bool:
    """¿Es '*' o '_' un delimitador de énfasis (no está dentro de una palabra)?"""
    antes = texto[i - 1] if i > 0 else " "
    despues = texto[i + 1] if i + 1 < len(texto) else " "
    return not (antes.isalnum() and despues.isalnum())


def inline(texto: str) -> list[dict]:
    salida: list[dict] = []
    b = it = False
    buf: list[str] = []

    def vaciar():
        if buf:
            t = "".join(buf)
            t = t.replace("---", "—").replace("--", "–").replace("~", " ")
            salida.append({"txt": t, "b": b, "i": it, "code": False})
            buf.clear()

    i, n = 0, len(texto)
    while i < n:
        c = texto[i]
        if c == "\\":
            if i + 1 >= n or texto[i + 1] in " \n":
                vaciar()
                salida.append({"salto": True})
                i += 2
            else:
                buf.append(texto[i + 1])
                i += 2
            continue
        if c == "`":
            fin = _saltar_raw(texto, i)
            vaciar()
            crudo = texto[i:fin].strip("`")
            salida.append({"txt": crudo, "b": b, "i": it, "code": True})
            i = fin
            continue
        if c == "$":
            fin = texto.find("$", i + 1)
            if fin != -1:
                vaciar()
                salida.append({"math": texto[i + 1:fin].strip()})
                i = fin + 1
                continue
        if c == "*" and _limite(texto, i, not b):
            vaciar()
            b = not b
            i += 1
            continue
        if c == "_" and _limite(texto, i, not it):
            vaciar()
            it = not it
            i += 1
            continue
        if c == "@":
            m = re.match(r"@([\w:.\-]+)", texto[i:])
            if m:
                clave = m.group(1).rstrip(".:-")
                vaciar()
                salida.append({"cita": clave})
                i += 1 + len(clave)
                continue
        if c == "<":
            m = re.match(r"<[\w:.\-]+>", texto[i:])
            if m:
                i += m.end()
                continue
        if c == "#":
            m = _RE_LLAMADA.match(texto, i)
            if m:
                (nombre, pos, _), fin = _leer_llamada(texto, i)
                vaciar()
                if nombre not in ("h", "v", "pagebreak", "colbreak"):
                    for a in pos:
                        if "contenido" in a:
                            salida.extend(inline(a["contenido"]))
                        elif "str" in a:
                            salida.append({"txt": a["str"], "b": b, "i": it, "code": False})
                i = fin
                continue
        buf.append(c)
        i += 1
    vaciar()
    return salida


# ============================================================================
#  Bloques
# ============================================================================

def _texto(v) -> str:
    if v is None:
        return ""
    for k in ("str", "contenido", "raw"):
        if k in v:
            return v[k]
    return ""


def _ruta_imagen(v) -> str | None:
    if v is None:
        return None
    if "str" in v:
        return v["str"]
    if v.get("llamada") == "image" and v["args"][1]:
        return _texto(v["args"][1][0])
    return None


def _porcentaje(v, defecto: float) -> float:
    m = re.match(r"([\d.]+)\s*%", _texto(v)) if v else None
    return float(m.group(1)) / 100 if m else defecto


def _raw_de_contenido(contenido: str) -> tuple[str, str]:
    m = re.search(r"(`{3,})([\w+#-]*)[ \t]*\n?(.*?)\1", contenido, re.S)
    if m:
        return m.group(3).rstrip("\n"), m.group(2)
    m = re.search(r"`([^`]*)`", contenido)
    return (m.group(1), "") if m else (contenido.strip(), "")


def _bloque_llamada(nombre: str, pos: list, nom: dict, leer_archivo) -> list[dict]:
    pie = lambda v: inline(_texto(v)) if v and _texto(v) else None  # noqa: E731
    if nombre == "captura":
        return [{"t": "figura", "ruta": _ruta_imagen(pos[0]) if pos else None,
                 "ancho": _porcentaje(nom.get("ancho"), 0.85),
                 "borde": _texto(nom.get("borde")) != "false",
                 "pie": pie(pos[1]) if len(pos) > 1 else None}]
    if nombre == "image":
        return [{"t": "figura", "ruta": _ruta_imagen({"llamada": "image", "args": ("", pos, nom)}),
                 "ancho": _porcentaje(nom.get("width"), 1.0), "borde": False, "pie": None}]
    if nombre == "figure":
        interno = pos[0] if pos else None
        ruta = _ruta_imagen(interno) if interno and interno.get("llamada") == "image" else None
        if ruta:
            return [{"t": "figura", "ruta": ruta, "ancho": 0.85, "borde": False, "pie": pie(nom.get("caption"))}]
        return parsear(_texto(interno), leer_archivo) if interno else []
    if nombre == "tabla":
        col = nom.get("columnas")
        if col is None:
            columnas = ["auto"]
        elif "tupla" in col:
            columnas = [_texto(c) for c in col["tupla"]]
        elif _texto(col).isdigit():
            columnas = ["1fr"] * int(_texto(col))
        else:
            columnas = ["auto"]
        enc = [inline(_texto(e)) for e in nom.get("encabezado", {}).get("tupla", [])]
        celdas = [inline(_texto(c)) for c in pos]
        if col is None:
            columnas = ["1fr"] * max(len(enc), 1)
        return [{"t": "tabla", "columnas": columnas, "encabezado": enc, "celdas": celdas,
                 "pie": pie(nom.get("pie"))}]
    if nombre == "codigo":
        lenguaje = _texto(nom.get("lenguaje")) if nom.get("lenguaje") and "str" in nom["lenguaje"] else ""
        desde = _texto(nom.get("desde")) if nom.get("desde") else ""
        if desde:
            codigo = leer_archivo(desde).rstrip()
            lenguaje = lenguaje or desde.rsplit(".", 1)[-1]
            titulo = desde.split("/")[-1]
        else:
            codigo, lang = _raw_de_contenido(_texto(pos[0])) if pos else ("", "")
            lenguaje = lenguaje or lang
            titulo = None
        t = nom.get("titulo")
        if t is not None:
            titulo = None if _texto(t) == "none" else (_texto(t) if "str" in t else titulo)
        return [{"t": "codigo", "codigo": codigo, "lenguaje": lenguaje, "titulo": titulo,
                 "pie": pie(nom.get("pie"))}]
    if nombre == "nota":
        titulo = inline(_texto(nom["titulo"])) if nom.get("titulo") else [{"txt": "Nota", "b": False, "i": False, "code": False}]
        return [{"t": "nota", "titulo": titulo, "inl": inline(_texto(pos[0])) if pos else []}]
    # Desconocido: se conserva el contenido que tenga.
    bloques = []
    for a in pos:
        if "contenido" in a:
            bloques.extend(parsear(a["contenido"], leer_archivo))
    return bloques


def parsear(src: str, leer_archivo=lambda ruta: "") -> list[dict]:
    """Convierte texto Typst (subconjunto) en una lista de bloques."""
    src = src.replace("\r\n", "\n")
    bloques: list[dict] = []
    parrafo: list[str] = []
    lista: list = []

    def cerrar():
        if parrafo:
            bloques.append({"t": "parrafo", "inl": inline(" ".join(parrafo))})
            parrafo.clear()
        if lista:
            bloques.append({"t": "lista", "items": [(nv, o, inline(" ".join(t))) for nv, o, t in lista]})
            lista.clear()

    def etiquetar(fin: int) -> int:
        m = _RE_ETIQUETA.match(src, fin)
        if m and bloques:
            bloques[-1]["etiqueta"] = m.group(1)
            return m.end()
        return fin

    i, n = 0, len(src)
    while i < n:
        fin_linea = src.find("\n", i)
        fin_linea = n if fin_linea == -1 else fin_linea
        linea = src[i:fin_linea]
        s = linea.strip()
        sangria = len(linea) - len(linea.lstrip(" \t"))

        if not s:
            cerrar()
            i = fin_linea + 1
            continue
        if s.startswith("//") or re.match(r"#(import|set|show|let|include)\b", s):
            cerrar()
            i = fin_linea + 1
            continue
        m = re.match(r"^<([\w:.\-]+)>$", s)
        if m and bloques:
            cerrar()
            bloques[-1]["etiqueta"] = m.group(1)
            i = fin_linea + 1
            continue
        if s.startswith("```"):
            cerrar()
            marca = re.match(r"`{3,}", s).group(0)
            lenguaje = s[len(marca):].strip()
            inicio = fin_linea + 1
            cierre = src.find(marca, inicio)
            cierre = n if cierre == -1 else cierre
            bloques.append({"t": "codigo", "codigo": src[inicio:cierre].rstrip("\n"), "lenguaje": lenguaje,
                            "titulo": None, "pie": None})
            fin = cierre + len(marca)
            i = src.find("\n", fin)
            i = n if i == -1 else i + 1
            continue
        m = re.match(r"^(=+)\s+(.*)$", s)
        if m and not lista:
            cerrar()
            texto = _RE_ETIQUETA.sub("", m.group(2))
            bloques.append({"t": "titulo", "nivel": len(m.group(1)), "inl": inline(texto)})
            i = fin_linea + 1
            continue
        m = re.match(r"^([-+])\s+(.*)$", s)
        if m:
            if parrafo:
                bloques.append({"t": "parrafo", "inl": inline(" ".join(parrafo))})
                parrafo.clear()
            lista.append([sangria // 2, m.group(1) == "+", [m.group(2)]])
            i = fin_linea + 1
            continue
        if lista and sangria > 0:  # continuación de un ítem
            lista[-1][2].append(s)
            i = fin_linea + 1
            continue
        if s.startswith("$") and re.match(r"^\$\s", s):
            cerrar()
            inicio = i + linea.index("$") + 1
            cierre = src.find("$", inicio)
            bloques.append({"t": "ecuacion", "math": src[inicio:cierre].strip()})
            i = etiquetar(cierre + 1)
            i = src.find("\n", i)
            i = n if i == -1 else i + 1
            continue
        if _RE_LLAMADA.match(s):
            cerrar()
            inicio = i + sangria
            (nombre, pos, nom), fin = _leer_llamada(src, inicio)
            bloques.extend(_bloque_llamada(nombre, pos, nom, leer_archivo))
            fin = etiquetar(fin)
            i = src.find("\n", fin)
            i = n if i == -1 else i + 1
            continue
        if lista:
            cerrar()
        parrafo.append(s)
        i = fin_linea + 1
    cerrar()
    return bloques


# ============================================================================
#  Matemáticas (aproximación en texto)
# ============================================================================

SIMBOLOS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "zeta": "ζ", "eta": "η",
    "theta": "θ", "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "phi": "φ", "chi": "χ", "psi": "ψ",
    "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π",
    "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
    "dot": "·", "times": "×", "div": "÷", "pm": "±", "infinity": "∞", "oo": "∞", "sum": "∑",
    "product": "∏", "integral": "∫", "partial": "∂", "nabla": "∇", "approx": "≈", "in": "∈",
    "forall": "∀", "exists": "∃", "dif": "d", "degree": "°",
}
OPERADORES = {"->": " → ", "=>": " ⇒ ", "<=": " ≤ ", ">=": " ≥ ", "!=": " ≠ ", "=": " = ",
              "+": " + ", "-": " − ", "<": " < ", ">": " > "}
FUNCIONES = {"sin", "cos", "tan", "log", "ln", "exp", "lim", "max", "min", "det"}


def math_segmentos(src: str) -> list[tuple[str, str, bool]]:
    """Convierte math de Typst a segmentos (texto, 'sub'|'sup'|'', cursiva)."""
    tokens = re.findall(r'"[^"]*"|[A-Za-z]+(?:\.[a-z]+)*|\d+(?:\.\d+)?|->|=>|<=|>=|!=|\S', src)

    def convertir(toks: list, vert: str = "") -> list:
        out, k = [], 0
        while k < len(toks):
            t = toks[k]
            if t in ("_", "^"):
                sub, k = grupo_en(toks, k + 1)
                out.extend(convertir(sub, "sub" if t == "_" else "sup"))
                continue
            if t.startswith('"'):
                out.append((t[1:-1], vert, False))
            elif t == "frac":
                args, k = grupo_en(toks, k + 1)
                partes = _split_tokens(args)
                out.extend(convertir(partes[0] if partes else [], vert))
                out.append(("/", vert, False))
                out.extend(convertir(partes[1] if len(partes) > 1 else [], vert))
                continue
            elif t == "sqrt":
                args, k = grupo_en(toks, k + 1)
                out.append(("√(", vert, False))
                out.extend(convertir(args, vert))
                out.append((")", vert, False))
                continue
            elif t.split(".")[0] in SIMBOLOS:
                base = t.split(".")[0]
                # letras griegas minúsculas en cursiva; operadores y mayúsculas rectos
                griega_min = base[0].islower() and base in SIMBOLOS and "α" <= SIMBOLOS[base] <= "ω"
                out.append((SIMBOLOS[base], vert, griega_min))
            elif t in FUNCIONES:
                out.append((t, vert, False))
            elif t.isalpha():
                out.append((t, vert, True))
            elif t in OPERADORES:
                out.append((OPERADORES[t] if not vert else OPERADORES[t].strip(), vert, False))
            else:
                out.append((t, vert, False))
            k += 1
        return out

    def grupo_en(toks, k):
        if k < len(toks) and toks[k] == "(":
            nivel, j = 0, k
            while j < len(toks):
                nivel += toks[j] == "("
                nivel -= toks[j] == ")"
                if nivel == 0:
                    return toks[k + 1:j], j + 1
                j += 1
            return toks[k + 1:], len(toks)
        return toks[k:k + 1], k + 1

    return convertir(tokens)


def _split_tokens(toks: list) -> list[list]:
    partes, actual, nivel = [], [], 0
    for t in toks:
        if t == "(":
            nivel += 1
        elif t == ")":
            nivel -= 1
        if t == "," and nivel == 0:
            partes.append(actual)
            actual = []
        else:
            actual.append(t)
    partes.append(actual)
    return partes
