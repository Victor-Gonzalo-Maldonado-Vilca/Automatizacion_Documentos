// ============================================================================
//  COMPONENTES DEL INFORME
//  Medidas extraídas de plantilla.docx (1 twip = 1/20 pt).
//  Los archivos de contenido de cada documento importan este módulo:
//    #import "/plantillas/informe-laboratorio/componentes.typ": *
// ============================================================================

#let tw(n) = n * 1pt / 20

// --- Datos de compilación --------------------------------------------------
// El generador (src/generar.py) pasa la ruta del JSON con los datos ya
// combinados (config/institucion.yaml + informe.yaml del documento).
#let _datos = json(sys.inputs.at("datos", default: "/plantillas/informe-laboratorio/vacio.json"))
#let estilo = _datos.at("estilo", default: (:))
#let dir-doc = _datos.at("dir", default: "/")

#let color-barra = rgb(estilo.at("color_barra", default: "#C8310E"))
#let color-texto-barra = rgb(estilo.at("color_texto_barra", default: "#FFFFFF"))
#let color-datos = rgb(estilo.at("color_datos", default: "#2F5496"))
#let fuente = estilo.at("fuente", default: "Calibri")
#let fuente-codigo = estilo.at("fuente_codigo", default: "Consolas")

// --- Medidas de la plantilla -------------------------------------------------
#let ancho-tabla = tw(10266)      // ancho de las tablas del cuerpo
#let celda-x = tw(108)            // margen interno horizontal de celda (Word)
#let trazo = 0.5pt + black        // borde "single sz=4"
#let alto-barra = tw(397)         // alto de las barras rojas
#let interlineado = 0.317em       // "múltiple 1.08" de Calibri
#let interlineado-simple = 0.221em

// Ruta absoluta (desde la raíz del proyecto) a un archivo del documento.
#let ruta(archivo) = {
  if archivo.starts-with("/") { archivo } else { dir-doc + "/" + archivo }
}

// Texto de un campo llenado: azul y cursiva, como en la plantilla.
#let dato(cuerpo) = text(fill: color-datos, style: "italic", size: 11pt, cuerpo)

// Bloque con alto mínimo: crece si el contenido es mayor (y entonces puede
// dividirse entre páginas).
#let bloque-min(alto, ancho: 100%, ..args, cuerpo) = context {
  let medido = measure(block(width: ancho-tabla, ..args, cuerpo)).height
  if medido < alto {
    block(width: ancho, height: alto, breakable: false, ..args, cuerpo)
  } else {
    block(width: ancho, breakable: true, ..args, cuerpo)
  }
}

// Barra roja de sección (INFORMACIÓN BÁSICA, SOLUCIÓN Y RESULTADOS, ...).
#let barra(titulo) = block(
  width: 100%, height: alto-barra, fill: color-barra, stroke: trazo,
  above: 0pt, below: 0pt, sticky: true,
  align(center + horizon, text(
    fill: color-texto-barra, weight: "bold", size: 12pt,
    top-edge: "cap-height", bottom-edge: "baseline", titulo,
  )),
)

// ============================================================================
//  COMPONENTES PARA EL CONTENIDO
// ============================================================================

// Captura / imagen numerada con borde fino.
//   #captura("imagenes/escena.png", [Escena en ejecución]) <fig:escena>
#let captura(archivo, pie, ancho: 85%, borde: true) = {
  let img = if type(archivo) == str { image(ruta(archivo), width: 100%) } else { archivo }
  figure(
    box(width: ancho, stroke: if borde { trazo } else { none }, img),
    caption: pie,
    kind: image,
  )
}

// Tabla con el mismo estilo del informe: encabezado rojo, bordes negros.
//   #tabla(
//     columnas: (auto, 1fr),
//     encabezado: ([Propiedad], [Descripción]),
//     [Time.deltaTime], [Tiempo entre frames],
//     pie: [Propiedades de la clase Time],
//   )
#let tabla(columnas: auto, encabezado: (), alinear: left + horizon, pie: none, ..celdas) = {
  let n = if columnas == auto { calc.max(encabezado.len(), 1) } else if type(columnas) == int { columnas } else { columnas.len() }
  let cols = if columnas == auto { (1fr,) * n } else { columnas }
  let t = table(
    columns: cols,
    stroke: trazo,
    inset: (x: celda-x, y: 4pt),
    align: alinear,
    fill: (_, y) => if y == 0 and encabezado.len() > 0 { color-barra },
    ..if encabezado.len() > 0 {
      (table.header(..encabezado.map(e => align(center + horizon,
        text(fill: color-texto-barra, weight: "bold", e)))),)
    },
    ..celdas.pos(),
  )
  if pie == none { t } else { figure(t, caption: pie, kind: table) }
}

// Bloque de código. Acepta un bloque ```lang ...``` o un archivo:
//   #codigo(titulo: "Rotador.cs")[```cs ... ```]
//   #codigo(desde: "codigo/Rotador.cs")
#let codigo(..args, desde: none, lenguaje: auto, titulo: auto, pie: none) = {
  let contenido = if desde != none {
    let ext = desde.split(".").last()
    raw(read(ruta(desde)).trim(at: end), block: true, lang: if lenguaje == auto { ext } else { lenguaje })
  } else { args.pos().at(0, default: none) }
  let tit = if titulo == auto { if desde != none { desde.split("/").last() } else { none } } else { titulo }
  let caja = block(width: 100%, breakable: true, above: 8pt, below: 8pt, {
    if tit != none {
      block(width: 100%, fill: color-barra, stroke: trazo, inset: (x: 6pt, y: 3pt), above: 0pt, below: 0pt, sticky: true,
        text(fill: color-texto-barra, weight: "bold", size: 9pt, font: fuente-codigo, tit))
    }
    // El recuadro gris lo agrega la regla de raw en estilo-contenido.
    set block(above: 0pt)
    contenido
  })
  if pie == none { caja } else { figure(caja, caption: pie, kind: raw, supplement: [Código]) }
}

// Recuadro destacado (notas, observaciones).
#let nota(titulo: [Nota], cuerpo) = block(
  width: 100%, inset: (left: 8pt, rest: 6pt), above: 8pt, below: 8pt,
  stroke: (left: 2.5pt + color-barra, rest: 0.5pt + luma(190)),
  fill: color-barra.lighten(94%),
  [#text(weight: "bold", fill: color-barra, titulo): #cuerpo],
)

// Estilos aplicados dentro de las celdas de contenido.
#let estilo-contenido(cuerpo) = {
  set text(size: 11pt, fill: black, style: "normal")
  set par(justify: true, leading: interlineado, spacing: 8pt)
  show heading: set text(size: 11pt, weight: "bold")
  show heading: set block(above: 10pt, below: 6pt)
  show heading.where(level: 2): set text(style: "italic")
  set list(indent: 4pt, body-indent: 6pt)
  set enum(indent: 4pt, body-indent: 6pt)

  // Figuras
  set figure(gap: 6pt)
  show figure: set block(above: 10pt, below: 10pt)
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: table): set block(breakable: true)
  show figure.caption: it => text(size: 10pt, {
    text(weight: "bold", [#it.supplement #context it.counter.display(it.numbering).])
    [ ]
    it.body
  })

  // Código
  show raw: set text(font: fuente-codigo, size: 9.5pt)
  show raw.where(block: true): set text(size: 9pt)
  show raw.where(block: true): set par(justify: false, leading: 0.45em)
  show raw.where(block: true): it => block(width: 100%, fill: luma(247), stroke: 0.5pt + luma(160),
    inset: 7pt, breakable: true, align(left, it))
  show raw.where(block: false): box.with(fill: luma(240), inset: (x: 2pt), outset: (y: 2pt), radius: 1pt)
  show raw.line: it => if it.count > 1 {
    box(width: 1.8em, align(right, text(fill: luma(140), str(it.number))))
    h(0.8em)
    it.body
  } else { it }

  // Ecuaciones numeradas, con la fuente matemática de Word
  set math.equation(numbering: "(1)", supplement: [Ecuación])
  show math.equation: set text(font: "Cambria Math")

  cuerpo
}
