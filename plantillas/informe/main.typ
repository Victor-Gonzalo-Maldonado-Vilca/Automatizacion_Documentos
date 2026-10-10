// ============================================================================
//  PLANTILLA: INFORME DE LABORATORIO (réplica de plantilla.docx)
//  No se edita por documento: todo sale del JSON generado por src/generar.py
//    typst compile --root . --input datos=/.build/<doc>.json plantillas/informe/main.typ
// ============================================================================

#import "componentes.typ": *

#let d = _datos
#let inst = d.at("institucion", default: (:))
#let fmt = d.at("formato", default: (:))
#let info = d.at("informacion", default: (:))
#let et = d.at("etiquetas", default: (:))
#let doc-meta = d.at("documento", default: (:))

#let etiqueta(clave, defecto) = et.at(clave, default: defecto)
#let txt(v) = if v == none { "" } else { str(v) }
#let lista(v) = if v == none or v == "" { () } else if type(v) == array { v } else { (v,) }

// Contenido de una sección: archivo .typ (include) o texto en línea (markup).
#let cargar(valor) = {
  if valor == none or valor == "" { return none }
  let v = str(valor).trim()
  if v.ends-with(".typ") {
    include ruta(v)
  } else {
    eval(v, mode: "markup", scope: (
      dato: dato, captura: captura, tabla: tabla, codigo: codigo, nota: nota,
    ))
  }
}

#set document(
  title: txt(info.at("titulo", default: "")),
  author: lista(info.at("integrantes", default: ())).map(str),
)

#set text(font: fuente, size: 11pt, lang: "es", region: "PE",
  top-edge: "ascender", bottom-edge: "descender")
#set par(leading: interlineado, spacing: 8pt)

// ---------------------------------------------------------------------------
//  ENCABEZADO (se repite en cada página)
// ---------------------------------------------------------------------------
#let encabezado = {
  set text(size: 8pt, weight: "bold")
  set par(leading: interlineado-simple, spacing: 0pt, justify: false)
  table(
    columns: (tw(3119), tw(4962), tw(2126)),
    rows: (tw(983), tw(281), tw(258)),
    stroke: trazo,
    inset: (x: celda-x, y: 0pt),
    align: center + horizon,
    {
      let logo = inst.at("logo_izquierdo", default: none)
      if logo != none and logo != "" { image("/" + logo, width: 4.21cm, height: 1.73cm, fit: "contain") }
    },
    text(size: 9pt)[
      #txt(inst.at("universidad", default: "")) \
      #txt(inst.at("facultad", default: "")) \
      #txt(inst.at("escuela", default: ""))
    ],
    {
      let logo = inst.at("logo_derecho", default: none)
      if logo != none and logo != "" { image("/" + logo, height: 1.40cm, fit: "contain") }
    },
    table.cell(colspan: 3)[
      Formato: #text(weight: "regular", txt(fmt.at("nombre", default: "")))
    ],
    [Aprobación:  #txt(fmt.at("aprobacion", default: ""))],
    [Código: #txt(fmt.at("codigo", default: ""))],
    align(right)[Página: #text(weight: "regular", context counter(page).display())],
  )
}

#set page(
  paper: "a4",
  // Márgenes de Word ajustados por la sangría -289 twips de las tablas;
  // el superior incluye el alto real del encabezado (como lo hace Word).
  margin: (left: tw(1080 - 289), right: tw(11906 - 791 - 10266), top: tw(2498), bottom: tw(1276)),
  header-ascent: tw(268),
  header: encabezado,
)

// ---------------------------------------------------------------------------
//  TÍTULO
// ---------------------------------------------------------------------------
#align(center, text(size: 16pt, weight: "bold",
  txt(doc-meta.at("tipo", default: "INFORME DE LABORATORIO"))))

// ---------------------------------------------------------------------------
//  INFORMACIÓN BÁSICA
// ---------------------------------------------------------------------------
#let lbl(cuerpo) = text(size: 12pt, weight: "bold", cuerpo)
#let alto-fila = tw(544)

// Celda con alto mínimo de la plantilla (544 twips) y contenido centrado.
#let fila-min(cuerpo, alinear: horizon) = layout(size => {
  let m = measure(block(width: size.width, cuerpo)).height
  block(width: 100%, height: calc.max(m + 2pt, alto-fila), align(alinear, cuerpo))
})

#{
  set par(leading: interlineado-simple, spacing: 0pt, justify: false)
  let integrantes = lista(info.at("integrantes", default: ()))
  let docentes = lista(info.at("docentes", default: ()))
  let nota-val = txt(info.at("nota", default: ""))
  let col = (1782, 1693, 1761, 1681, 1681, 1668).map(tw)

  block(width: ancho-tabla, above: 8pt, below: 0pt, barra(etiqueta("informacion_basica", "INFORMACIÓN BÁSICA")))
  table(
    columns: col,
    stroke: trazo,
    inset: (x: celda-x, y: 0pt),
    align: left + horizon,
    // ASIGNATURA
    fila-min(lbl[#etiqueta("asignatura", "ASIGNATURA:")]),
    table.cell(colspan: 5, fila-min(dato(txt(info.at("asignatura", default: ""))))),
    // TÍTULO
    fila-min(lbl[#etiqueta("titulo", "TÍTULO DE LA PRÁCTICA:")]),
    table.cell(colspan: 5, fila-min(dato(txt(info.at("titulo", default: ""))))),
    // NÚMERO / AÑO / SEMESTRE
    fila-min(lbl[#etiqueta("numero", "NÚMERO DE PRÁCTICA:")]),
    fila-min(dato(txt(info.at("numero", default: "")))),
    fila-min(lbl[#etiqueta("anio_lectivo", "AÑO LECTIVO:")]),
    fila-min(dato(txt(info.at("anio_lectivo", default: "")))),
    fila-min(lbl[#etiqueta("semestre", "NRO. SEMESTRE:")]),
    fila-min(dato(txt(info.at("semestre", default: "")))),
    // FECHA / HORA
    fila-min(lbl[#etiqueta("fecha", "FECHA DE PRESENTACIÓN")]),
    fila-min(dato(txt(info.at("fecha", default: "")))),
    fila-min(lbl[#etiqueta("hora", "HORA DE PRESENTACIÓN")]),
    table.cell(colspan: 3, fila-min(dato(txt(info.at("hora", default: ""))))),
    // INTEGRANTES / NOTA
    table.cell(colspan: 4, align: left + top, inset: (x: celda-x, top: 1pt, bottom: 3pt), {
      lbl[#etiqueta("integrantes", "INTEGRANTE (s):")]
      // La plantilla reserva dos líneas para los nombres.
      let filas = integrantes.map(i => dato(str(i)))
      while filas.len() < 2 { filas.push(text(size: 12pt)[#h(0pt)]) }
      for f in filas { linebreak(); f }
    }),
    fila-min(lbl[#etiqueta("nota", "NOTA:")]),
    fila-min(dato(nota-val)),
    // DOCENTES
    table.cell(colspan: 6, inset: (x: celda-x, top: 1pt), fila-min(alinear: top, {
      lbl[#etiqueta("docentes", "DOCENTE(s):") ]
      dato(docentes.map(str).join(", "))
    })),
  )
}

// Párrafo vacío entre tablas (Calibri 11 pt, 1.08, 8 pt después).
#let separador = v(tw(160) + 11pt * (1 + interlineado.em), weak: false)

// ---------------------------------------------------------------------------
//  SECCIONES
// ---------------------------------------------------------------------------
#let romano(n) = numbering("I", n)

// Encabezado de apartado: "I.  TÍTULO" (número alineado a la derecha).
#let titulo-apartado(n, titulo) = block(above: 0pt, below: 4pt, sticky: true, {
  set par(justify: false, leading: interlineado-simple)
  grid(
    columns: (tw(180), tw(322 - 180), 1fr),
    align(right, text(size: 12pt, weight: "bold", romano(n) + ".")),
    [],
    text(size: 12pt, weight: "bold", titulo),
  )
})

// Preguntas del cuestionario: viñetas en azul cursiva, con su respuesta.
#let preguntas(items) = {
  for p in items {
    let pregunta = if type(p) == dictionary { p.at("pregunta", default: "") } else { p }
    let respuesta = if type(p) == dictionary { p.at("respuesta", default: none) } else { none }
    block(above: 4pt, below: 4pt, sticky: respuesta != none, pad(left: 38.6pt, grid(
      columns: (11pt, 1fr),
      text(size: 11pt)[•],
      par(justify: true, dato(str(pregunta))),
    )))
    let r = cargar(respuesta)
    if r != none { block(above: 4pt, below: 10pt, pad(left: 49.6pt, r)) }
  }
}

#let caja-apartado(alto, cuerpo) = bloque-min(
  alto,
  stroke: trazo,
  inset: (left: celda-x, right: celda-x, top: 3pt, bottom: 6pt),
  above: 0pt, below: 0pt,
  cuerpo,
)

#let seccion(s) = {
  let titulo = txt(s.at("titulo", default: ""))
  let apartados = s.at("apartados", default: none)
  block(width: ancho-tabla, above: 0pt, below: 0pt, sticky: true, barra(titulo))

  if apartados != none and apartados.len() > 0 {
    let n = 0
    for a in apartados {
      n += 1
      let alto = a.at("alto_minimo", default: none)
      let alto = if alto == none or alto == "" { tw(if n == 1 { 1353 } else { 1088 }) } else { float(alto) * 1cm }
      caja-apartado(alto, estilo-contenido({
        titulo-apartado(n, txt(a.at("titulo", default: "")))
        block(above: 0pt, pad(left: tw(322), {
          let p = a.at("preguntas", default: none)
          if p != none and p.len() > 0 { pad(left: -tw(322), preguntas(p)) }
          let c = cargar(a.at("contenido", default: none))
          if c != none { c }
        }))
      }))
    }
  } else {
    let alto = s.at("alto_minimo", default: none)
    let alto = if alto == none or alto == "" { tw(1088) } else { float(alto) * 1cm }
    caja-apartado(alto, estilo-contenido({
      v(4pt)
      let c = cargar(s.at("contenido", default: none))
      if c != none { c }
    }))
  }
  separador
}

#separador
#for s in d.at("secciones", default: ()) { seccion(s) }

// ---------------------------------------------------------------------------
//  REFERENCIAS (IEEE)
// ---------------------------------------------------------------------------
#{
  let ref = d.at("referencias", default: (:))
  let titulo = txt(ref.at("titulo", default: "REFERENCIAS Y BIBLIOGRAFÍA"))
  let archivo = ref.at("archivo", default: none)
  block(width: ancho-tabla, above: 0pt, below: 0pt, sticky: true, barra(titulo))
  caja-apartado(tw(1441), {
    set text(size: 11pt)
    set par(justify: true, leading: interlineado-simple, spacing: 6pt)
    // IEEE usa comillas inglesas también en español.
    show "«": "“"
    show "»": "”"
    v(2pt)
    // Solo si el .bib tiene al menos una entrada (Typst no acepta uno vacío).
    if archivo != none and archivo != "" and read(ruta(archivo)).contains("@") {
      bibliography(ruta(archivo), title: none, style: ref.at("estilo", default: "ieee"),
        full: ref.at("incluir_todas", default: "false") == "true")
    }
  })
}
