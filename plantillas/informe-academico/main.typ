// ============================================================================
//  PLANTILLA: INFORME ACADÉMICO (portada + índice + secciones + referencias)
//  No se edita por documento: todo sale del JSON generado por src/generar.py
// ============================================================================

#import "componentes.typ": *

#let d = _datos
#let por = d.at("portada", default: (:))
#let inst = d.at("institucion", default: (:))
#let ind = d.at("indice", default: (:))
#let ref = d.at("referencias", default: (:))

#let txt(v) = if v == none { "" } else { str(v) }
#let lista(v) = if v == none or v == "" { () } else if type(v) == array { v.filter(x => x != "") } else { (v,) }
#let si(v, defecto: true) = if v == none or v == "" { defecto } else { str(v) == "true" }
#let etq(clave, defecto) = por.at("etiquetas", default: (:)).at(clave, default: defecto)

#let cargar(valor) = {
  if valor == none or valor == "" { return none }
  let v = str(valor).trim()
  if v.ends-with(".typ") { include ruta(v) } else {
    eval(v, mode: "markup", scope: (captura: captura, tabla: tabla, codigo: codigo, nota: nota))
  }
}

#set document(title: txt(por.at("titulo", default: "")), author: lista(por.at("miembros", default: ())).map(str))
#set page(paper: "a4", margin: 2.54cm)
#show: estilo-documento

#let numeracion = txt(d.at("numeracion_titulos", default: ""))
#set heading(numbering: if numeracion == "" or numeracion == "none" { none } else { numeracion })

// ---------------------------------------------------------------------------
//  PORTADA (Times New Roman 12 pt, interlineado 1.5, centrada)
// ---------------------------------------------------------------------------
#{
  set align(center)
  set text(size: 12pt)
  set par(justify: false, first-line-indent: 0pt, leading: 0.62em, spacing: 0.62em)
  let renglon = v(12pt * 1.725, weak: false)
  let universidad = txt(por.at("universidad", default: inst.at("universidad", default: "")))
  let facultad = txt(por.at("facultad", default: inst.at("facultad", default: "")))
  let escuela = txt(por.at("escuela", default: inst.at("escuela", default: "")))
  strong[#universidad \ #facultad \ #escuela]
  renglon
  let logo = txt(por.at("logo", default: inst.at("logo_portada", default: "")))
  if logo != "" { image("/" + logo, width: 4.63cm) }
  renglon
  [*#txt(por.at("tipo", default: "INFORME"))* \ #txt(por.at("titulo", default: ""))]
  renglon
  let curso = txt(por.at("curso", default: ""))
  if curso != "" { [*#etq("curso", "CURSO:")* \ #curso]; renglon }
  let docentes = lista(por.at("docentes", default: ()))
  if docentes.len() > 0 { [*#etq("docentes", "DOCENTE:")* \ #docentes.map(str).join(linebreak())]; renglon }
  let miembros = lista(por.at("miembros", default: ()))
  if miembros.len() > 0 { [*#etq("miembros", "MIEMBROS:")* \ #miembros.map(str).join(linebreak())]; renglon }
  strong[#txt(por.at("lugar", default: "")) \ #txt(por.at("anio", default: ""))]
}

// Desde aquí, número de página centrado al pie (la portada no lo muestra).
#set page(footer: context align(center, text(size: 10pt, counter(page).display())))
#pagebreak()

// ---------------------------------------------------------------------------
//  ÍNDICE
// ---------------------------------------------------------------------------
#if si(ind.at("mostrar", default: "true")) {
  let profundidad = int(txt(ind.at("profundidad", default: "2")))
  align(center, text(size: 12pt, weight: "bold", txt(ind.at("titulo", default: "ÍNDICE"))))
  v(10pt)
  {
    set par(first-line-indent: 0pt, justify: false)
    outline(title: none, depth: profundidad, indent: 1.2em)
  }
  if si(ind.at("figuras", default: "false"), defecto: false) {
    v(18pt)
    align(center, text(size: 12pt, weight: "bold")[ÍNDICE DE FIGURAS])
    v(6pt)
    outline(title: none, target: figure.where(kind: image))
  }
  if si(ind.at("tablas", default: "false"), defecto: false) {
    v(18pt)
    align(center, text(size: 12pt, weight: "bold")[ÍNDICE DE TABLAS])
    v(6pt)
    outline(title: none, target: figure.where(kind: table))
  }
  pagebreak()
}

// ---------------------------------------------------------------------------
//  SECCIONES
//  El título de cada sección es nivel 1; dentro del contenido, "=" es nivel 2.
// ---------------------------------------------------------------------------
#for s in d.at("secciones", default: ()) {
  if si(s.at("nueva_pagina", default: "false"), defecto: false) { pagebreak(weak: true) }
  heading(level: 1, txt(s.at("titulo", default: "")))
  {
    set heading(offset: 1)
    let c = cargar(s.at("contenido", default: none))
    if c != none { c }
  }
}

// ---------------------------------------------------------------------------
//  REFERENCIAS
// ---------------------------------------------------------------------------
#{
  let archivo = txt(ref.at("archivo", default: ""))
  if archivo != "" and read(ruta(archivo)).contains("@") {
    heading(level: 1, txt(ref.at("titulo", default: "REFERENCIAS")))
    set par(first-line-indent: 0pt, spacing: 8pt)
    show "«": "“"
    show "»": "”"
    bibliography(ruta(archivo), title: none, style: txt(ref.at("estilo", default: "ieee")),
      full: si(ref.at("incluir_todas", default: "false"), defecto: false))
  }
}
