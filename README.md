# Automatización de Documentos Académicos

Genera, desde archivos de texto:

- el **informe de laboratorio** con el formato oficial GUIA-PRLE-001,
- el **informe académico** con portada, índice y referencias,
- **presentaciones** académicas con temas de color intercambiables.

Los informes salen en **PDF** y **Word**; las presentaciones en **PPTX** y **PDF**.

## Requisitos

- Python 3.10 o superior
- [Typst](https://typst.app) (`winget install --id Typst.Typst`), para el informe en PDF
- Microsoft PowerPoint o LibreOffice, solo para exportar presentaciones a PDF
- Dependencias de Python:

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Interfaz gráfica

```powershell
.\.venv\Scripts\python interfaz.py
```

Se abre en el navegador (`http://127.0.0.1:5000`, solo accesible desde esta PC):

- **Lista de documentos** con buscador y botón **Nuevo documento** (elige el formato y la carpeta).
- **Datos:** formulario generado a partir del YAML (listas, secciones, diapositivas…).
  Al guardar se conservan los comentarios y el formato del archivo.
- **Contenido:** editor de los `.typ` con botones para insertar subtítulos, listas,
  capturas, tablas, código, notas, ecuaciones y citas.
- **Imágenes:** subir arrastrando, ver la galería y copiar el código para insertarlas.
- **Referencias:** asistente para agregar referencias (web, libro, artículo…) y editor del `.bib`.
- **YAML:** edición directa del archivo de datos.
- **Generar:** elige las salidas (PDF, Word, PPTX) y el tema; el resultado se ve en la
  vista previa y se puede abrir o descargar.

La interfaz usa la misma lógica que la línea de comandos, así que ambas pueden usarse indistintamente.

## Uso desde la línea de comandos

Cada documento es un archivo YAML que declara su `formato:`. Los formatos son
**independientes**: se genera solo lo que se necesita.

```powershell
# Crear documentos
.\.venv\Scripts\python generar.py --nuevo informe-laboratorio documentos\lab07
.\.venv\Scripts\python generar.py --nuevo informe-academico documentos\proyecto
.\.venv\Scripts\python generar.py --nuevo presentacion documentos\exposicion

# Generar
.\.venv\Scripts\python generar.py documentos\lab07\informe.yaml       # un documento
.\.venv\Scripts\python generar.py documentos\lab07                     # todos los de la carpeta
.\.venv\Scripts\python generar.py documentos\lab07 --salida docx       # solo el Word
.\.venv\Scripts\python generar.py documentos\lab07 --salida pdf,docx   # PDF y Word juntos
.\.venv\Scripts\python generar.py documentos\exposicion --salida pdf   # presentación solo en PDF
.\.venv\Scripts\python generar.py documentos\lab07 --formato presentacion
.\.venv\Scripts\python generar.py documentos\exposicion --tema azul    # cambiar colores
.\.venv\Scripts\python generar.py --todos                               # todo lo de documentos/

# Consultar
.\.venv\Scripts\python generar.py --formatos
.\.venv\Scripts\python generar.py --temas
```

Los archivos generados quedan en `output/<carpeta>/`. Con `--abrir` se abren al terminar.

**Salidas:** sin `--salida` se generan las indicadas en `salidas:` del YAML
(por defecto, todas las del formato). En una carpeta con varios documentos,
`--salida` se aplica a los que pueden producirla y los demás se omiten.

## Formatos disponibles

| Formato | Archivo | Salidas |
|---|---|---|
| `informe-laboratorio` | `informe.yaml` | `pdf` (Typst), `docx` (sobre la plantilla Word original) |
| `informe-academico` | `informe.yaml` | `pdf` (Typst), `docx` (con índice actualizado por Word) |
| `presentacion` | `presentacion.yaml` | `pptx`, `pdf` (exportado con PowerPoint/LibreOffice) |

Una carpeta puede tener un solo documento o varios (por ejemplo, un informe y
la presentación del mismo trabajo). Con `--nuevo` se puede sumar un formato a
una carpeta que ya tiene otro.

## Estructura

```
generar.py                         Línea de comandos
interfaz.py                        Interfaz gráfica (abre el navegador)
config/institucion.yaml            Universidad, logos y encabezado (común a todos los formatos)
src/datos.py, src/bib.py           Utilidades comunes (YAML, BibTeX)
src/typst_lite.py                  Lector del contenido .typ para generar Word
src/docx_render.py                 Escritura del contenido en Word (común a los informes)
src/resaltado.py, src/office.py    Resaltado de código y conversión/actualización con Office
src/formatos/                      Un módulo por formato + registro (__init__.py)
src/web/                           Servidor de la interfaz (Flask) y página (HTML/CSS/JS)
plantillas/<formato>/              Diseño de cada formato y su esqueleto nuevo/
  informe-laboratorio/plantilla.docx   Plantilla Word oficial (base del .docx)
  informe-academico/plantilla.docx     Estilos de la plantilla académica, sin contenido
documentos/<carpeta>/              Tus documentos: *.yaml, contenido/, imagenes/, codigo/, referencias.bib
  ejemplo-laboratorio/             Informe de laboratorio con todos los componentes
  ejemplo-academico/               Informe académico con portada, índice, tablas y figuras
  ejemplo-presentacion/            Presentación independiente con todos los tipos de diapositiva
```

## Agregar un formato nuevo

1. Crear `src/formatos/<nombre>.py` con `NOMBRE`, `DESCRIPCION`, `ARCHIVO`,
   `PLANTILLA_NUEVO`, `SALIDAS` y `generar(ruta_yaml, salida, opciones) -> list[Path]`
   (las salidas elegidas llegan en `opciones["salidas"]`).
2. Registrarlo en la tupla de `src/formatos/__init__.py`.
3. Poner su diseño y su esqueleto en `plantillas/<nombre>/` y `plantillas/<nombre>/nuevo/`.

Los formatos existentes no se modifican.

## Informe de laboratorio (PDF y Word)

- **PDF:** lo compone Typst con la réplica del formato.
- **Word:** se construye sobre `plantilla.docx` copiando sus filas, barras, numeración y
  encabezado reales, así que conserva exactamente el formato y queda editable. El mismo
  contenido (`.typ`) se convierte a Word: capturas, tablas, código con colores, notas,
  listas, citas IEEE y referencias cruzadas. Las ecuaciones se escriben como texto con
  símbolos (θ, ω, Δ, subíndices), no como ecuaciones editables de Word.

**Datos generales:** todo lo de la tabla *Información básica* está en `informe.yaml`.
Los textos de la institución y del encabezado están en `config/institucion.yaml`;
cualquier clave se puede sobreescribir en el `informe.yaml` de un documento.

**Secciones:** cada elemento de `secciones` es una barra roja con su recuadro. Los
`apartados` se numeran I, II, III… Se pueden agregar, quitar o renombrar
secciones libremente. El `contenido` puede ser un archivo `.typ` o texto corto en el YAML.

**Etiquetas:** para otro tipo de documento (taller, proyecto…) se cambian las
etiquetas de la tabla en `informe.yaml`:

```yaml
documento: { tipo: INFORME DE TALLER }
etiquetas:
  titulo: "TÍTULO DEL TALLER:"
  numero: "NÚMERO DE TALLER:"
```

**Componentes para el contenido** (en archivos `contenido/*.typ`):

| Qué | Cómo |
|---|---|
| Subtítulo | `= Ejercicio 1` / `== Resultados` |
| Captura numerada | `#captura("imagenes/x.png", [Pie]) <fig:x>` |
| Tabla con estilo del informe | `#tabla(columnas: (auto, 1fr), encabezado: ([A], [B]), [1], [2], pie: [Pie])` |
| Código desde archivo | `#codigo(desde: "codigo/Script.cs", pie: [Descripción])` |
| Código en línea | ``#codigo(titulo: "x.py")[```py print(1)```]`` |
| Nota destacada | `#nota[Texto]` |
| Ecuación numerada | `$ E = m c^2 $ <eq:x>` |
| Cita IEEE | `@clave` (del `.bib`) |
| Referencia cruzada | `@fig:x`, `@tab:x`, `@eq:x` |
| Negrita / cursiva / código | `*negrita*`, `_cursiva_`, `` `código` `` |

## Informe académico (PDF y Word)

Réplica de la plantilla académica: portada centrada con el escudo (universidad,
facultad, escuela, título, curso, docente, miembros, lugar y año), cuerpo en Times
New Roman 11 pt justificado con sangría, tablas con encabezado durazno y bordes
grises ("**Tabla N.** Título" arriba) y figuras con pie "**Figura N** _descripción_".

```yaml
formato: informe-academico
portada:
  titulo: TÍTULO DEL INFORME
  curso: NOMBRE DEL CURSO
  docentes: [Mg. NOMBRE DEL DOCENTE]
  miembros: [INTEGRANTE 1, INTEGRANTE 2]
  lugar: AREQUIPA - PERÚ
  anio: 2026
indice:
  mostrar: true
  profundidad: 2      # niveles de títulos en el índice
  figuras: true       # índice de figuras
  tablas: true        # índice de tablas
secciones:
  - titulo: INTRODUCCIÓN
    contenido: contenido/01_introduccion.typ
  - titulo: ANEXOS
    nueva_pagina: true
    contenido: contenido/04_anexos.typ
referencias: { archivo: referencias.bib, estilo: ieee }
```

- **Secciones:** cada una es un título principal; dentro de su `.typ`, `= Subtítulo`
  y `== Subsubtítulo` (todos aparecen en el índice). Con `numeracion_titulos: "1.1."`
  se numeran automáticamente.
- **Índice:** en el PDF lo arma Typst. En Word es un índice real de Word (con
  hipervínculos): si Word está instalado se actualiza al generar; si no, Word pide
  actualizarlo al abrir el archivo.
- Se usan los mismos componentes que en el laboratorio (`#captura`, `#tabla`,
  `#codigo`, `#nota`, citas y ecuaciones), con el estilo de esta plantilla.
- **Páginas:** la portada no lleva número; desde el índice, número centrado al pie.

## Presentaciones (PPTX y PDF)

Tipos: `portada`, `agenda`, `seccion`, `contenido`, `dos_columnas`, `imagen`,
`tabla`, `codigo`, `destacado`, `metricas`, `referencias`, `cierre`.
Cualquier diapositiva admite `notas:` (notas del orador). Ver
`documentos/ejemplo-presentacion/presentacion.yaml`.

**Datos de portada:** la presentación es independiente y tiene sus propios datos:

```yaml
formato: presentacion
datos:
  etiqueta: Exposición académica
  titulo: Título de la exposición
  subtitulo: Curso o evento
  autores: [Nombre Apellido]
  docentes: [Nombre del docente]
  fecha: Octubre 2026
  referencias: referencias.bib
```

Si es la exposición de un informe de la misma carpeta, puede reutilizar sus
datos con `desde: informe.yaml` (lo escrito en `datos:` tiene prioridad).

**Colores:** `tema: azul` en `presentacion.yaml`, `--tema` en la línea de comandos,
o solo algunos colores:

```yaml
colores:
  primario: "#0B5394"
  acento: "#F1C232"
```

Temas incluidos: `unsa`, `azul`, `verde`, `vino`, `grafito`, `noche`.

## Consejos

- En YAML, los valores con `:` o que empiezan con `@`, `*`, `[` o `{` van entre comillas.
- Para previsualizar el informe mientras se escribe, en VS Code se puede instalar la extensión **Tinymist** y usar:
  `typst watch --root . --input datos=/.build/<carpeta>-informe.json plantillas/informe-laboratorio/main.typ`
  (el `.json` se crea al ejecutar `generar.py` una vez).

## Autoría

Proyecto desarrollado por **Victor Gonzalo Maldonado Vilca** en colaboración
con **Claude** (modelo Claude Opus 5.5 de Anthropic), usado como asistente de
desarrollo en Claude Code.

| Autor | Aporte |
|---|---|
| **Victor Gonzalo Maldonado Vilca** | Idea y objetivo del proyecto, definición de requisitos y formatos de documento, selección de las plantillas institucionales, decisiones de diseño, dirección del desarrollo, pruebas y revisión de resultados |
| **Claude** (Anthropic) | Implementación del código y de las plantillas (Typst, Word y PowerPoint), propuestas de arquitectura y redacción de la documentación, a partir de los requisitos y la revisión del autor |

El formato original del informe de laboratorio (GUIA-PRLE-001) pertenece a la
Escuela Profesional de Ingeniería de Sistemas – UNSA. Los logos de la escuela,
de la universidad y de ABET pertenecen a sus respectivos titulares y se incluyen
solo para reproducir los formatos institucionales.

En el historial de Git, los primeros commits figuran con Claude como autor; los
siguientes tienen como autor a Victor Gonzalo Maldonado Vilca y a Claude como
coautor (`Co-Authored-By`).
