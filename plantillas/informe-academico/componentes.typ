// ============================================================================
//  COMPONENTES DEL INFORME ACADÉMICO
//  Estilo extraído de la plantilla (Times New Roman 11 pt, tablas con
//  encabezado durazno y bordes grises, pies de figura estilo APA).
//  Los archivos de contenido importan este módulo:
//    #import "/plantillas/informe-academico/componentes.typ": *
// ============================================================================

#let _datos = json(sys.inputs.at("datos", default: "/plantillas/informe-academico/vacio.json"))
#let estilo = _datos.at("estilo", default: (:))
#let dir-doc = _datos.at("dir", default: "/")

#let fuente = estilo.at("fuente", default: "Times New Roman")
#let fuente-codigo = estilo.at("fuente_codigo", default: "Consolas")
#let color-encabezado = rgb(estilo.at("color_encabezado", default: "#FCE5CD"))
#let color-texto-encabezado = rgb(estilo.at("color_texto_encabezado", default: "#000000"))
#let color-borde = rgb(estilo.at("color_borde", default: "#C4C7C5"))
#let color-acento = rgb(estilo.at("color_acento", default: "#B45F06"))

// Times New Roman: interlineado 1.15 de Word y un renglón en blanco entre párrafos.
#let interlineado = 0.22em
#let espacio-parrafo = 14.5pt
#let sangria = 1.27cm
#let trazo = 0.6pt + color-borde

#let ruta(archivo) = {
  if archivo.starts-with("/") { archivo } else { dir-doc + "/" + archivo }
}

// Captura / imagen numerada (sin borde, como en la plantilla).
//   #captura("imagenes/diagrama.png", [Diagrama de contexto]) <fig:contexto>
#let captura(archivo, pie, ancho: 85%, borde: false) = {
  let img = if type(archivo) == str { image(ruta(archivo), width: 100%) } else { archivo }
  figure(box(width: ancho, stroke: if borde { 0.5pt + black } else { none }, img), caption: pie, kind: image)
}

// Tabla con el estilo de la plantilla.
#let tabla(columnas: auto, encabezado: (), alinear: left + top, pie: none, ..celdas) = {
  let n = if columnas == auto { calc.max(encabezado.len(), 1) } else if type(columnas) == int { columnas } else { columnas.len() }
  let cols = if columnas == auto { (1fr,) * n } else if type(columnas) == int { (1fr,) * columnas } else { columnas }
  let t = {
    set text(size: 10pt)
    set par(justify: false, first-line-indent: 0pt, leading: interlineado)
    table(
      columns: cols,
      stroke: trazo,
      inset: (x: 9pt, y: 6pt),
      align: alinear,
      fill: (_, y) => if y == 0 and encabezado.len() > 0 { color-encabezado },
      ..if encabezado.len() > 0 {
        (table.header(..encabezado.map(e => text(fill: color-texto-encabezado, weight: "bold", e))),)
      },
      ..celdas.pos(),
    )
  }
  if pie == none { t } else { figure(t, caption: pie, kind: table) }
}

// Bloque de código (en línea o desde archivo).
#let codigo(..args, desde: none, lenguaje: auto, titulo: auto, pie: none) = {
  let contenido = if desde != none {
    let ext = desde.split(".").last()
    raw(read(ruta(desde)).trim(at: end), block: true, lang: if lenguaje == auto { ext } else { lenguaje })
  } else { args.pos().at(0, default: none) }
  let tit = if titulo == auto { if desde != none { desde.split("/").last() } else { none } } else { titulo }
  let caja = block(width: 100%, breakable: true, above: 8pt, below: 8pt, {
    if tit != none {
      block(width: 100%, fill: color-encabezado, stroke: trazo, inset: (x: 6pt, y: 3pt), above: 0pt, below: 0pt,
        sticky: true, text(fill: color-texto-encabezado, weight: "bold", size: 9pt, font: fuente-codigo, tit))
    }
    set block(above: 0pt)
    contenido
  })
  if pie == none { caja } else { figure(caja, caption: pie, kind: raw, supplement: [Código]) }
}

// Recuadro destacado.
#let nota(titulo: [Nota], cuerpo) = block(
  width: 100%, inset: (left: 8pt, rest: 6pt), above: 8pt, below: 8pt,
  stroke: (left: 2.5pt + color-acento, rest: trazo),
  fill: color-encabezado.lighten(50%),
  par(first-line-indent: 0pt)[#text(weight: "bold", fill: color-acento, titulo): #cuerpo],
)

// Estilos de todo el documento.
#let estilo-documento(cuerpo) = {
  set text(font: fuente, size: 11pt, lang: "es", region: "PE",
    top-edge: "ascender", bottom-edge: "descender")
  set par(justify: true, leading: interlineado, spacing: espacio-parrafo,
    first-line-indent: (amount: sangria, all: true))
  set list(marker: ([•], [◦]), indent: 0.1cm, body-indent: 0.45cm, spacing: 0.6em)
  set enum(indent: 0.1cm, body-indent: 0.45cm, spacing: 0.6em)
  show list: set par(first-line-indent: 0pt)
  show enum: set par(first-line-indent: 0pt)

  // Títulos: 1 = secciones del YAML; 2 y 3 = "=" y "==" dentro del contenido
  show heading: set text(size: 11pt, weight: "bold")
  show heading: set par(justify: false)
  show heading.where(level: 1): set text(size: 12pt)
  show heading.where(level: 1): set block(above: 24pt, below: 14pt)
  show heading.where(level: 2): set block(above: 16pt, below: 10pt)
  show heading.where(level: 3): set block(above: 14pt, below: 8pt)
  show heading.where(level: 3): set text(style: "italic")

  // Figuras y pies
  set figure(gap: 8pt)
  show figure: set block(above: 14pt, below: 14pt)
  show figure: set par(first-line-indent: 0pt)
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: table): set block(breakable: true)
  show figure.caption: it => context {
    let n = it.counter.display(it.numbering)
    if it.kind == table {
      align(left, text(weight: "bold")[#it.supplement #n. #it.body])
    } else {
      [#text(weight: "bold")[#it.supplement #n] #emph(it.body)]
    }
  }

  // Código
  show raw: set text(font: fuente-codigo, size: 9.5pt)
  show raw.where(block: true): set text(size: 9pt)
  show raw.where(block: true): set par(justify: false, leading: 0.45em, first-line-indent: 0pt)
  show raw.where(block: true): it => block(width: 100%, fill: luma(248), stroke: trazo,
    inset: 7pt, breakable: true, align(left, it))
  show raw.where(block: false): box.with(fill: luma(240), inset: (x: 2pt), outset: (y: 2pt), radius: 1pt)
  show raw.line: it => if it.count > 1 {
    box(width: 1.8em, align(right, text(fill: luma(140), str(it.number))))
    h(0.8em)
    it.body
  } else { it }

  // Ecuaciones
  set math.equation(numbering: "(1)", supplement: [Ecuación])
  show math.equation: set text(font: "Cambria Math")

  // Índice
  show outline.entry.where(level: 1): set text(weight: "bold")
  show outline.entry.where(level: 1): set block(above: 10pt)

  cuerpo
}
