"use strict";

/* ==========================================================================
   Interfaz del generador de documentos
   Todo el estado vive en E; las vistas se vuelven a dibujar desde él.
   ========================================================================== */

const E = {
  estado: null,        // formatos, temas y tipos de diapositiva
  docs: [],            // lista de documentos
  doc: null,           // documento abierto (respuesta de /api/documento)
  datos: null,         // datos editables del documento (copia)
  sucio: false,        // datos sin guardar
  pestana: "datos",
  archivo: null,       // {ruta, texto, sucio} abierto en Contenido/Referencias
  generados: [],
  vista: null,         // ruta del archivo mostrado en la vista previa
  abiertos: new Set(), // tarjetas desplegadas (por camino)
};

const NOMBRE_FORMATO = {
  "informe-laboratorio": "Informe de laboratorio",
  "informe-academico": "Informe académico",
  "presentacion": "Presentación",
};

const ETIQUETAS = {
  documento: "Documento", informacion: "Información básica", portada: "Portada", datos: "Datos de portada",
  indice: "Índice", secciones: "Secciones", apartados: "Apartados", preguntas: "Preguntas",
  referencias: "Referencias", diapositivas: "Diapositivas", opciones: "Opciones", colores: "Colores",
  etiquetas: "Etiquetas", estilo: "Estilo", institucion: "Institución", encabezado: "Encabezado",
  tipo: "Tipo", titulo: "Título", subtitulo: "Subtítulo", archivo: "Archivo", asignatura: "Asignatura",
  numero: "Número", anio_lectivo: "Año lectivo", anio: "Año", semestre: "Semestre", fecha: "Fecha",
  hora: "Hora", integrantes: "Integrantes", nota: "Nota", docentes: "Docentes", miembros: "Miembros",
  autores: "Autores", curso: "Curso", lugar: "Lugar", universidad: "Universidad", facultad: "Facultad",
  escuela: "Escuela", logo: "Logo", contenido: "Contenido", pregunta: "Pregunta", respuesta: "Respuesta",
  alto_minimo: "Alto mínimo (cm)", mostrar: "Mostrar", profundidad: "Profundidad", figuras: "Índice de figuras",
  tablas: "Índice de tablas", nueva_pagina: "Empieza en página nueva", numeracion_titulos: "Numeración de títulos",
  incluir_todas: "Incluir todas las referencias", tema: "Tema", puntos: "Puntos", texto: "Texto",
  destacado: "Franja destacada", notas: "Notas del orador", imagen: "Imagen", pie: "Pie", izquierda: "Columna izquierda",
  derecha: "Columna derecha", encabezado_tabla: "Encabezado", filas: "Filas", anchos: "Anchos de columna",
  codigo: "Código", lenguaje: "Lenguaje", nombre: "Nombre", items: "Indicadores", valor: "Valor",
  etiqueta: "Etiqueta", detalle: "Detalle", claves: "Claves", contacto: "Contacto", desde: "Datos desde",
  numeracion: "Numerar diapositivas", barra_progreso: "Barra de progreso", mostrar_seccion: "Mostrar sección",
  logo_en_diapositivas: "Logo en diapositivas", sub: "Subpuntos", primario: "Primario", acento: "Acento",
};

const SINGULAR = {
  secciones: "sección", apartados: "apartado", preguntas: "pregunta", diapositivas: "diapositiva",
  integrantes: "integrante", docentes: "docente", miembros: "miembro", autores: "autor", puntos: "punto",
  items: "indicador", filas: "fila", claves: "clave", encabezado: "columna", sub: "subpunto",
};

const BOOLEANOS = new Set(["mostrar", "figuras", "tablas", "nueva_pagina", "incluir_todas", "numeracion",
  "barra_progreso", "mostrar_seccion", "logo_en_diapositivas"]);
const LARGOS = new Set(["texto", "notas", "destacado", "contacto"]);
const ARCHIVOS = { contenido: "contenido", respuesta: "contenido", imagen: "imagenes", logo: "imagenes",
  desde: "todos", archivo: "todos" };
const OCULTOS_RAIZ = new Set(["formato", "salidas"]);

/* --- utilidades ------------------------------------------------------------ */

const $ = (s, r = document) => r.querySelector(s);

function el(etiqueta, attrs = {}, ...hijos) {
  const n = document.createElement(etiqueta);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (k === "dataset") Object.assign(n.dataset, v);
    else if (v === true) n.setAttribute(k, "");
    else n.setAttribute(k, v);
  }
  for (const h of hijos.flat()) if (h !== null && h !== undefined && h !== false) n.append(h);
  return n;
}

async function api(metodo, url, cuerpo) {
  const opciones = { method: metodo, headers: {} };
  if (cuerpo instanceof FormData) opciones.body = cuerpo;
  else if (cuerpo !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(cuerpo);
  }
  const r = await fetch(url, opciones);
  let datos = null;
  try { datos = await r.json(); } catch { /* respuesta vacía */ }
  if (!r.ok) throw new Error((datos && datos.error) || `Error ${r.status}`);
  return datos;
}

function aviso(texto, tipo = "") {
  const a = el("div", { class: `aviso ${tipo}`, text: texto });
  $("#avisos").append(a);
  setTimeout(() => a.remove(), tipo === "error" ? 7000 : 3200);
}

const etiqueta = (k) => ETIQUETAS[k] || String(k).replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
const esObjeto = (v) => v && typeof v === "object" && !Array.isArray(v);
const clonar = (v) => JSON.parse(JSON.stringify(v));
const urlArchivo = (ruta, descargar) => `/archivos/${ruta.split("/").map(encodeURIComponent).join("/")}${descargar ? "?descargar=1" : `?t=${Date.now()}`}`;

function marcarSucio(v = true) {
  E.sucio = v;
  const s = $("#estado-guardado");
  s.textContent = v ? "Cambios sin guardar" : "Guardado";
  s.classList.toggle("pendiente", v);
  $("#btn-guardar").disabled = !v;
}

/* --- inicio ------------------------------------------------------------------ */

async function iniciar() {
  E.estado = await api("GET", "/api/estado");
  await cargarDocumentos();
  $("#buscar").addEventListener("input", dibujarLista);
  $("#btn-nuevo").addEventListener("click", abrirDialogoNuevo);
  $("#btn-guardar").addEventListener("click", () => guardar());
  $("#btn-generar").addEventListener("click", generar);
  $("#tema").addEventListener("change", (ev) => {
    E.datos.tema = ev.target.value;
    marcarSucio();
    if (E.pestana === "datos") dibujarDatos();
  });
  document.querySelectorAll(".pestanas button").forEach((b) =>
    b.addEventListener("click", () => cambiarPestana(b.dataset.pestana)));
  document.addEventListener("keydown", (ev) => {
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "s") {
      ev.preventDefault();
      if (E.archivo && E.archivo.sucio && ["archivos", "referencias"].includes(E.pestana)) guardarArchivo();
      else if (E.sucio) guardar();
    }
  });
  window.addEventListener("beforeunload", (ev) => {
    if (E.sucio || (E.archivo && E.archivo.sucio)) { ev.preventDefault(); ev.returnValue = ""; }
  });
  // Enlace directo: #doc=documentos/x/informe.yaml&pestana=datos
  const hash = new URLSearchParams(location.hash.slice(1));
  let inicial = hash.get("doc");
  if (!inicial) {
    try { inicial = localStorage.getItem("ultimoDocumento"); } catch { inicial = null; }
  }
  if (inicial && E.docs.some((d) => d.ruta === inicial)) {
    await abrirDocumento(inicial);
    if (hash.get("pestana")) cambiarPestana(hash.get("pestana"));
    if (hash.get("archivo")) { cambiarPestana("archivos"); await abrirArchivo(`${E.doc.carpeta}/${hash.get("archivo")}`); }
  }
}

async function cargarDocumentos() {
  E.docs = await api("GET", "/api/documentos");
  dibujarLista();
}

function dibujarLista() {
  const filtro = $("#buscar").value.trim().toLowerCase();
  const nav = $("#lista-documentos");
  nav.replaceChildren();
  const grupos = {};
  for (const d of E.docs) {
    const texto = `${d.titulo} ${d.carpeta} ${d.formato}`.toLowerCase();
    if (filtro && !texto.includes(filtro)) continue;
    (grupos[d.carpeta] ||= []).push(d);
  }
  for (const [carpeta, docs] of Object.entries(grupos)) {
    nav.append(el("div", { class: "grupo-carpeta" }, el("h4", { text: carpeta }),
      docs.map((d) => el("button", {
        class: `item-doc ${E.doc && E.doc.ruta === d.ruta ? "activo" : ""}`,
        onclick: () => abrirDocumento(d.ruta), title: d.ruta,
      }, el("span", { class: "t", text: d.titulo }),
        el("span", { class: "m" }, el("span", { class: `punto ${d.formato}` }),
          `${NOMBRE_FORMATO[d.formato] || d.formato} · ${d.archivo}`)))));
  }
  if (!nav.children.length) nav.append(el("p", { class: "ayuda", text: "No hay documentos." }));
}

/* --- documento ------------------------------------------------------------------ */

function hayCambios() {
  return E.sucio || (E.archivo && E.archivo.sucio);
}

async function abrirDocumento(ruta, { forzar = false } = {}) {
  if (!forzar && E.doc && E.doc.ruta !== ruta && hayCambios() &&
      !confirm("Hay cambios sin guardar. ¿Descartarlos y abrir otro documento?")) return;
  try {
    const d = await api("GET", `/api/documento?ruta=${encodeURIComponent(ruta)}`);
    const otro = !E.doc || E.doc.ruta !== d.ruta;
    E.doc = d;
    E.datos = clonar(d.datos);
    if (otro) { E.abiertos = new Set(); E.archivo = null; E.vista = null; }
    E.generados = d.generados;
    try { localStorage.setItem("ultimoDocumento", d.ruta); } catch { /* sin almacenamiento */ }
    history.replaceState(null, "", `#doc=${d.ruta}`);
    $("#vacio").classList.add("oculto");
    $("#editor").classList.remove("oculto");
    marcarSucio(false);
    dibujarCabecera();
    dibujarPestana();
    dibujarResultado();
    dibujarLista();
  } catch (e) { aviso(e.message, "error"); }
}

function tituloDe(datos) {
  return (datos.informacion && datos.informacion.titulo) || (datos.portada && datos.portada.titulo) ||
    (datos.datos && datos.datos.titulo) || E.doc.carpeta.split("/").pop();
}

function dibujarCabecera() {
  const d = E.doc;
  const insignia = $("#doc-formato");
  insignia.className = `insignia ${d.formato}`;
  insignia.textContent = NOMBRE_FORMATO[d.formato] || d.formato;
  $("#doc-titulo").textContent = tituloDe(E.datos);
  $("#doc-ruta").textContent = d.ruta;
  const chips = $("#chips-salidas");
  chips.replaceChildren(...d.salidas_posibles.map((s) => el("label", { class: "chip" },
    el("input", { type: "checkbox", value: s, checked: d.salidas_defecto.includes(s) }), s)));
  const esPresentacion = d.formato === "presentacion";
  $("#selector-tema").classList.toggle("oculto", !esPresentacion);
  if (esPresentacion) {
    $("#tema").replaceChildren(...E.estado.temas.map((t) =>
      el("option", { value: t.clave, text: t.nombre, selected: (E.datos.tema || "unsa") === t.clave })));
  }
}

async function guardar({ silencioso = false } = {}) {
  if (!E.doc) return;
  try {
    const r = await api("POST", "/api/documento", { ruta: E.doc.ruta, datos: E.datos });
    E.doc.yaml = r.yaml;
    E.doc.datos = r.datos;
    E.datos = clonar(r.datos);
    marcarSucio(false);
    $("#doc-titulo").textContent = tituloDe(E.datos);
    // El formulario debe apuntar a los datos nuevos; si no, los cambios
    // posteriores se escribirían en la copia anterior y no se guardarían.
    if (E.pestana === "datos") dibujarDatos();
    if (!silencioso) aviso("Datos guardados", "ok");
    if (E.pestana === "yaml") dibujarPestana();
    cargarDocumentos();
  } catch (e) { aviso(e.message, "error"); throw e; }
}

function cambiarPestana(p) {
  if (E.archivo && E.archivo.sucio && !confirm("El archivo abierto tiene cambios sin guardar. ¿Descartarlos?")) return;
  if (E.pestana !== p) E.archivo = null;
  E.pestana = p;
  document.querySelectorAll(".pestanas button").forEach((b) => b.classList.toggle("activa", b.dataset.pestana === p));
  document.querySelectorAll(".panel").forEach((x) => x.classList.add("oculto"));
  $(`#panel-${p}`).classList.remove("oculto");
  dibujarPestana();
}

async function dibujarPestana() {
  const p = E.pestana;
  if (p === "datos") dibujarDatos();
  else if (p === "archivos") dibujarArchivos();
  else if (p === "imagenes") dibujarImagenes();
  else if (p === "referencias") dibujarReferencias();
  else if (p === "yaml") {
    if (E.sucio) { try { await guardar({ silencioso: true }); } catch { return; } }
    dibujarYaml();
  }
}

/* --- formulario de datos ---------------------------------------------------------- */

function dibujarDatos() {
  const panel = $("#panel-datos");
  const scroll = panel.scrollTop;
  panel.replaceChildren();
  const generales = {};
  const bloques = [];
  for (const [k, v] of Object.entries(E.datos)) {
    if (OCULTOS_RAIZ.has(k)) continue;
    if (esObjeto(v) || Array.isArray(v)) bloques.push(k);
    else generales[k] = v;
  }
  if (Object.keys(generales).length) {
    const cuerpo = el("div", { class: "tarjeta-cuerpo" });
    cuerpo.append(...filaCampos(E.datos, Object.keys(generales), []).filter(Boolean));
    panel.append(tarjeta("General", cuerpo, "raiz:general", true));
  }
  bloques.forEach((k, i) => {
    const v = E.datos[k];
    const cuerpo = el("div", { class: "tarjeta-cuerpo" });
    if (Array.isArray(v)) cuerpo.append(editorLista(E.datos, k, [k]));
    else cuerpo.append(editorDict(v, [k]));
    panel.append(tarjeta(etiqueta(k), cuerpo, `raiz:${k}`, i < 3));
  });
  panel.scrollTop = scroll;
}

function tarjeta(titulo, cuerpo, clave, abiertaPorDefecto) {
  const abierta = E.abiertos.has(clave) || (abiertaPorDefecto && !E.abiertos.has(`!${clave}`));
  const d = el("details", { class: "tarjeta", open: abierta }, el("summary", { text: titulo }), cuerpo);
  d.addEventListener("toggle", () => {
    E.abiertos.delete(d.open ? `!${clave}` : clave);
    E.abiertos.add(d.open ? clave : `!${clave}`);
  });
  return d;
}

function filaCampos(obj, claves, camino) {
  const fila = el("div", { class: "campo-fila" });
  const anchos = [];
  for (const k of claves) {
    const control = editorEscalar(obj, k, [...camino, k]);
    const largo = control.tagName === "TEXTAREA" || (control.querySelector && control.querySelector("textarea"));
    const nombre = k === "archivo" && (camino.length === 0 || camino[0] === "documento")
      ? "Nombre de los archivos generados" : etiqueta(k);
    const c = el("div", { class: "campo" }, el("label", { text: nombre }), control);
    if (largo) anchos.push(c); else fila.append(c);
  }
  return [fila.children.length ? fila : null, ...anchos.map((c) => { c.style.gridColumn = "1 / -1"; return c; })];
}

function editorDict(obj, camino) {
  const cont = el("div", { class: "tarjeta-cuerpo", style: "padding:0" });
  const escalares = [];
  const vaciar = () => { if (escalares.length) { cont.append(...filaCampos(obj, escalares.splice(0), camino).filter(Boolean)); } };
  for (const [k, v] of Object.entries(obj)) {
    if (esObjeto(v)) {
      vaciar();
      const clave = [...camino, k].join(".");
      const d = el("details", { class: "subtarjeta", open: !E.abiertos.has(`!${clave}`) },
        el("summary", {}, el("span", { class: "titulo-item", text: etiqueta(k) })),
        el("div", { class: "tarjeta-cuerpo" }, editorDict(v, [...camino, k])));
      d.addEventListener("toggle", () => { if (d.open) E.abiertos.delete(`!${clave}`); else E.abiertos.add(`!${clave}`); });
      cont.append(d);
    } else if (Array.isArray(v)) {
      vaciar();
      cont.append(el("div", { class: "campo" }, el("label", { text: etiqueta(k) }), editorLista(obj, k, [...camino, k])));
    } else {
      escalares.push(k);
    }
  }
  vaciar();
  cont.append(el("button", {
    class: "boton chico agregar", type: "button", text: "+ Campo",
    title: "Agregar un campo a este grupo (por ejemplo: notas, alto_minimo, nueva_pagina)",
    onclick: () => {
      const nombre = (prompt("Nombre del campo (en minúsculas, sin espacios):") || "").trim();
      if (!nombre) return;
      if (nombre in obj) { aviso("Ese campo ya existe", "error"); return; }
      obj[nombre] = "";
      marcarSucio();
      dibujarDatos();
    },
  }));
  return cont;
}

function opcionesArchivos(tipo) {
  const a = E.doc.archivos;
  if (tipo === "contenido") return a.contenido;
  if (tipo === "imagenes") return a.imagenes;
  return [...a.contenido, ...a.codigo, ...a.bib, ...a.imagenes];
}

function editorEscalar(obj, k, camino) {
  const semantica = typeof k === "number" ? camino[camino.length - 2] : k;
  const valor = obj[k] ?? "";
  const asignar = (v) => {
    obj[k] = v;
    marcarSucio();
    if (semantica === "titulo" && camino.length <= 2) $("#doc-titulo").textContent = tituloDe(E.datos);
  };

  if (BOOLEANOS.has(semantica) || valor === "true" || valor === "false") {
    const caja = el("input", { type: "checkbox", checked: valor === "true",
      onchange: (ev) => asignar(ev.target.checked ? "true" : "false") });
    return el("label", { class: "interruptor" }, caja, el("span", { text: "Sí" }));
  }
  const seleccion = (opciones) => el("select", { onchange: (ev) => asignar(ev.target.value) },
    opciones.map(([v, t]) => el("option", { value: v, text: t, selected: v === valor })));
  if (semantica === "tipo" && camino.includes("diapositivas")) {
    const s = seleccion(E.estado.tipos_diapositiva.map((t) => [t, t.replace("_", " ")]));
    s.addEventListener("change", () => {
      // Agrega los campos propios del nuevo tipo (sin borrar los existentes).
      for (const [c, v] of Object.entries(CAMPOS_DIAPOSITIVA[obj.tipo] || {})) if (!(c in obj)) obj[c] = clonar(v);
      dibujarDatos();
    });
    return s;
  }
  if (semantica === "tema") {
    const s = seleccion(E.estado.temas.map((t) => [t.clave, t.nombre]));
    s.addEventListener("change", () => { $("#tema").value = obj[k]; });
    return s;
  }
  if (semantica === "estilo" && camino[0] === "referencias") {
    return seleccion([["ieee", "IEEE"], ["apa", "APA (solo PDF)"]]);
  }
  if (semantica === "profundidad") return seleccion([["1", "1 nivel"], ["2", "2 niveles"], ["3", "3 niveles"]]);

  if (LARGOS.has(semantica) || String(valor).length > 80) {
    return el("textarea", { oninput: (ev) => asignar(ev.target.value) }, String(valor));
  }
  const input = el("input", { type: "text", value: valor, oninput: (ev) => asignar(ev.target.value) });
  const tipoArchivo = ARCHIVOS[semantica];
  if (tipoArchivo && typeof k === "string") {
    const id = `dl-${tipoArchivo}`;
    if (!document.getElementById(id)) document.body.append(el("datalist", { id }));
    const lista = document.getElementById(id);
    lista.replaceChildren(...opcionesArchivos(tipoArchivo).map((f) => el("option", { value: f })));
    input.setAttribute("list", id);
    input.placeholder = tipoArchivo === "contenido" ? "archivo .typ o texto corto" : "ruta del archivo";
    if (String(valor).endsWith(".typ")) {
      return el("div", { class: "con-boton" }, input, el("button", {
        class: "boton chico", type: "button", text: "Editar",
        onclick: () => { cambiarPestana("archivos"); abrirArchivo(`${E.doc.carpeta}/${obj[k]}`); },
      }));
    }
  }
  return input;
}

function plantillaVacia(v) {
  if (Array.isArray(v)) return v.length ? [plantillaVacia(v[0])] : [];
  if (esObjeto(v)) {
    const o = {};
    for (const [k, x] of Object.entries(v)) o[k] = k === "tipo" ? x : plantillaVacia(x);
    return o;
  }
  return "";
}

const CAMPOS_DIAPOSITIVA = {
  agenda: { titulo: "Contenido" },
  seccion: { titulo: "", subtitulo: "" },
  contenido: { titulo: "", texto: "", puntos: [""], destacado: "" },
  dos_columnas: { titulo: "", izquierda: { subtitulo: "", puntos: [""] }, derecha: { subtitulo: "", puntos: [""] } },
  imagen: { titulo: "", imagen: "", pie: "", puntos: [""] },
  tabla: { titulo: "", pie: "", encabezado: ["", ""], filas: [["", ""]] },
  codigo: { titulo: "", archivo: "", puntos: [""] },
  destacado: { texto: "", autor: "" },
  metricas: { titulo: "", items: [{ valor: "", etiqueta: "", detalle: "" }] },
  referencias: { titulo: "Referencias" },
  cierre: { titulo: "¡Gracias!", subtitulo: "¿Preguntas?" },
};

function nuevoElemento(clave, arr) {
  if (clave === "diapositivas") return { tipo: "contenido", ...clonar(CAMPOS_DIAPOSITIVA.contenido) };
  if (clave === "preguntas") return { pregunta: "", respuesta: "" };
  if (arr.length) return plantillaVacia(arr[arr.length - 1]);
  return "";
}

function resumen(item, i) {
  if (!esObjeto(item)) return `#${i + 1}`;
  const t = item.titulo || item.pregunta || item.texto || item.etiqueta || item.valor || "";
  return t ? String(t) : `#${i + 1}`;
}

function editorLista(padre, clave, camino) {
  if (!Array.isArray(padre[clave])) padre[clave] = padre[clave] ? [padre[clave]] : [];
  const arr = padre[clave];
  const cont = el("div", { class: "lista" });
  const redibujar = () => { const nuevo = editorLista(padre, clave, camino); cont.replaceWith(nuevo); };
  const mover = (i, d) => { const j = i + d; if (j < 0 || j >= arr.length) return; [arr[i], arr[j]] = [arr[j], arr[i]]; marcarSucio(); redibujar(); };
  const quitar = (i) => { arr.splice(i, 1); marcarSucio(); redibujar(); };
  const herramientas = (i) => el("span", { class: "herramientas-item" },
    el("button", { class: "boton icono chico", type: "button", title: "Subir", text: "↑", onclick: (ev) => { ev.preventDefault(); mover(i, -1); } }),
    el("button", { class: "boton icono chico", type: "button", title: "Bajar", text: "↓", onclick: (ev) => { ev.preventDefault(); mover(i, 1); } }),
    el("button", { class: "boton icono chico peligro", type: "button", title: "Quitar", text: "✕", onclick: (ev) => { ev.preventDefault(); quitar(i); } }));

  arr.forEach((item, i) => {
    if (esObjeto(item) || Array.isArray(item)) {
      const llave = [...camino, i].join(".");
      const titulo = el("span", { class: "titulo-item" }, `${i + 1}. ${resumen(item, i)}`,
        esObjeto(item) && item.tipo ? el("small", { text: item.tipo }) : null);
      const cuerpo = Array.isArray(item)
        ? editorLista(arr, i, [...camino, i])
        : editorDict(item, [...camino, i]);
      const d = el("details", { class: "subtarjeta", open: E.abiertos.has(llave) },
        el("summary", {}, titulo, herramientas(i)), el("div", { class: "tarjeta-cuerpo" }, cuerpo));
      d.addEventListener("toggle", () => { if (d.open) E.abiertos.add(llave); else E.abiertos.delete(llave); });
      d.addEventListener("input", () => { titulo.firstChild.textContent = `${i + 1}. ${resumen(item, i)}`; });
      cont.append(d);
    } else {
      cont.append(el("div", { class: "fila-lista" }, el("span", { class: "num", text: `${i + 1}.` }),
        editorEscalar(arr, i, [...camino, i]), herramientas(i)));
    }
  });
  const nombre = SINGULAR[clave] || "elemento";
  cont.append(el("button", {
    class: "boton chico agregar", type: "button", text: `+ Agregar ${nombre}`,
    onclick: () => {
      arr.push(nuevoElemento(clave, arr));
      E.abiertos.add([...camino, arr.length - 1].join("."));
      marcarSucio();
      redibujar();
    },
  }));
  return cont;
}

/* --- contenido (.typ y código) ------------------------------------------------------ */

const FRAGMENTOS = [
  ["Subtítulo", () => "= Subtítulo\n\n"],
  ["Lista", () => "- Primer punto\n- Segundo punto\n"],
  ["Captura", () => `#captura("${E.doc.archivos.imagenes[0] || "imagenes/archivo.png"}", [Descripción de la figura]) <fig:etiqueta>\n`],
  ["Tabla", () => "#tabla(\n  columnas: (auto, 1fr),\n  encabezado: ([Columna 1], [Columna 2]),\n  [Dato], [Dato],\n  [Dato], [Dato],\n  pie: [Título de la tabla],\n) <tab:etiqueta>\n"],
  ["Código", () => `#codigo(desde: "${E.doc.archivos.codigo[0] || "codigo/archivo.py"}", pie: [Descripción del código])\n`],
  ["Nota", () => "#nota[Texto de la nota.]\n"],
  ["Ecuación", () => "$ y = m x + b $ <eq:etiqueta>\n"],
];

function insertar(area, texto) {
  const { selectionStart: a, selectionEnd: b, value } = area;
  area.value = value.slice(0, a) + texto + value.slice(b);
  area.selectionStart = area.selectionEnd = a + texto.length;
  area.focus();
  area.dispatchEvent(new Event("input"));
}

function areaEditor(texto, alCambiar) {
  const area = el("textarea", { class: "editor-texto", spellcheck: "false" });
  area.value = texto;
  area.addEventListener("input", () => alCambiar(area.value));
  area.addEventListener("keydown", (ev) => {
    if (ev.key === "Tab") { ev.preventDefault(); insertar(area, "  "); }
  });
  return area;
}

async function clavesBib() {
  const claves = [];
  for (const b of E.doc.archivos.bib) {
    try {
      const r = await api("GET", `/api/archivo?ruta=${encodeURIComponent(`${E.doc.carpeta}/${b}`)}`);
      for (const m of r.texto.matchAll(/@\w+\s*\{\s*([^,\s]+)\s*,/g)) claves.push(m[1]);
    } catch { /* sin referencias */ }
  }
  return claves;
}

async function abrirArchivo(ruta) {
  if (E.archivo && E.archivo.sucio && E.archivo.ruta !== ruta &&
      !confirm("El archivo abierto tiene cambios sin guardar. ¿Descartarlos?")) return;
  try {
    const r = await api("GET", `/api/archivo?ruta=${encodeURIComponent(ruta)}`);
    E.archivo = { ruta: r.ruta, texto: r.texto, sucio: false };
    dibujarPestana();
  } catch (e) { aviso(e.message, "error"); }
}

async function guardarArchivo() {
  if (!E.archivo) return;
  try {
    await api("POST", "/api/archivo", { ruta: E.archivo.ruta, texto: E.archivo.texto });
    E.archivo.sucio = false;
    aviso("Archivo guardado", "ok");
    dibujarPestana();
  } catch (e) { aviso(e.message, "error"); }
}

async function refrescarArchivos() {
  const d = await api("GET", `/api/documento?ruta=${encodeURIComponent(E.doc.ruta)}`);
  E.doc.archivos = d.archivos;
}

async function nuevoArchivo() {
  const esInforme = E.doc.formato !== "presentacion";
  const nombre = (prompt("Ruta del nuevo archivo dentro de la carpeta del documento:",
    esInforme ? "contenido/nuevo.typ" : "codigo/ejemplo.py") || "").trim();
  if (!nombre) return;
  const texto = nombre.endsWith(".typ") ? `#import "/plantillas/${E.doc.formato}/componentes.typ": *\n\n` : "";
  try {
    await api("POST", "/api/archivo", { ruta: `${E.doc.carpeta}/${nombre}`, texto, crear: true });
    await refrescarArchivos();
    await abrirArchivo(`${E.doc.carpeta}/${nombre}`);
    if (nombre.endsWith(".typ")) aviso("Archivo creado. Agrégalo a una sección en la pestaña Datos (campo Contenido).");
  } catch (e) { aviso(e.message, "error"); }
}

function barraArchivo(extra) {
  const a = E.archivo;
  return el("div", { class: "barra-editor" },
    el("span", { class: "nombre", text: a.ruta.replace(`${E.doc.carpeta}/`, "") + (a.sucio ? " •" : "") }),
    ...extra,
    el("button", { class: "boton chico primario", type: "button", text: "Guardar", disabled: !a.sucio, onclick: guardarArchivo }));
}

async function dibujarArchivos() {
  const panel = $("#panel-archivos");
  const { contenido, codigo } = E.doc.archivos;
  const grupo = (titulo, lista) => lista.length ? [el("h4", { text: titulo }), ...lista.map((f) => {
    const ruta = `${E.doc.carpeta}/${f}`;
    return el("button", { class: `archivo-item ${E.archivo && E.archivo.ruta === ruta ? "activo" : ""}`, text: f, title: f, onclick: () => abrirArchivo(ruta) });
  })] : [];
  const lista = el("div", { class: "lista-archivos" },
    el("button", { class: "boton chico", type: "button", text: "+ Nuevo archivo", onclick: nuevoArchivo }),
    ...grupo("Contenido", contenido), ...grupo("Código", codigo));

  let area;
  if (E.archivo) {
    const esTyp = E.archivo.ruta.endsWith(".typ");
    area = areaEditor(E.archivo.texto, (v) => {
      E.archivo.texto = v;
      if (!E.archivo.sucio) { E.archivo.sucio = true; panel.querySelector(".barra-editor").replaceWith(barra()); }
    });
    const claves = esTyp ? await clavesBib() : [];
    const barra = () => barraArchivo(esTyp ? [
      ...FRAGMENTOS.map(([t, f]) => el("button", { class: "boton chico", type: "button", text: t, onclick: () => insertar(area, f()) })),
      claves.length ? el("select", { class: "boton chico", title: "Insertar cita",
        onchange: (ev) => { if (ev.target.value) insertar(area, `@${ev.target.value}`); ev.target.value = ""; } },
        el("option", { value: "", text: "Cita…" }), claves.map((c) => el("option", { value: c, text: c }))) : null,
    ] : []);
    panel.replaceChildren(el("div", { class: "dividido" }, lista, el("div", { class: "area-editor" }, barra(), area)));
  } else {
    const mensaje = E.doc.formato === "presentacion"
      ? "Las presentaciones se editan en la pestaña Datos. Aquí puedes crear o editar archivos de código para las diapositivas de tipo código."
      : "Elige un archivo para editar el contenido de una sección.";
    panel.replaceChildren(el("div", { class: "dividido" }, lista,
      el("div", { class: "area-editor" }, el("p", { class: "ayuda", style: "margin:auto;padding:30px;text-align:center", text: mensaje }))));
  }
}

/* --- imágenes ---------------------------------------------------------------------- */

async function subirArchivos(archivos) {
  if (!archivos.length) return;
  const fd = new FormData();
  fd.append("carpeta", E.doc.carpeta);
  fd.append("subcarpeta", "imagenes");
  for (const f of archivos) fd.append("archivos", f);
  try {
    const r = await api("POST", "/api/subir", fd);
    aviso(`${r.guardados.length} imagen(es) agregada(s)`, "ok");
    await refrescarArchivos();
    dibujarImagenes();
  } catch (e) { aviso(e.message, "error"); }
}

function dibujarImagenes() {
  const panel = $("#panel-imagenes");
  const entrada = el("input", { type: "file", accept: "image/*", multiple: true, class: "oculto",
    onchange: (ev) => subirArchivos([...ev.target.files]) });
  const zona = el("div", { class: "zona-subir", onclick: () => entrada.click() },
    el("strong", { text: "Arrastra imágenes aquí o haz clic para elegirlas" }),
    el("span", { class: "ayuda", text: "Se guardan en la carpeta imagenes/ del documento." }), entrada);
  zona.addEventListener("dragover", (ev) => { ev.preventDefault(); zona.classList.add("encima"); });
  zona.addEventListener("dragleave", () => zona.classList.remove("encima"));
  zona.addEventListener("drop", (ev) => { ev.preventDefault(); zona.classList.remove("encima"); subirArchivos([...ev.dataTransfer.files]); });

  const esPresentacion = E.doc.formato === "presentacion";
  const galeria = el("div", { class: "galeria" }, E.doc.archivos.imagenes.map((img) => {
    const codigo = esPresentacion ? img : `#captura("${img}", [Descripción de la figura])`;
    return el("div", { class: "imagen-tarjeta" },
      el("img", { src: urlArchivo(`${E.doc.carpeta}/${img}`), alt: img, loading: "lazy" }),
      el("div", { class: "pie" }, el("span", { text: img, title: img }),
        el("div", { class: "con-boton" },
          el("button", { class: "boton chico", type: "button", text: esPresentacion ? "Copiar ruta" : "Copiar código",
            onclick: async () => { await navigator.clipboard.writeText(codigo); aviso(`Copiado: ${codigo}`); } }),
          el("button", { class: "boton chico peligro", type: "button", text: "Borrar",
            onclick: async () => {
              if (!confirm(`¿Borrar ${img}?`)) return;
              await api("DELETE", `/api/archivo?ruta=${encodeURIComponent(`${E.doc.carpeta}/${img}`)}`);
              await refrescarArchivos();
              dibujarImagenes();
            } }))));
  }));
  panel.replaceChildren(zona, E.doc.archivos.imagenes.length ? galeria : el("p", { class: "ayuda", text: "Todavía no hay imágenes." }));
}

/* --- referencias --------------------------------------------------------------------- */

const TIPOS_REF = {
  online: { nombre: "Página web", campos: [["url", "URL"], ["urldate", "Fecha de acceso", "date"], ["organization", "Organización"]] },
  book: { nombre: "Libro", campos: [["publisher", "Editorial"], ["address", "Ciudad, país"], ["edition", "Edición"]] },
  article: { nombre: "Artículo de revista", campos: [["journal", "Revista"], ["volume", "Volumen"], ["number", "Número"], ["pages", "Páginas"]] },
  inproceedings: { nombre: "Artículo de congreso", campos: [["booktitle", "Congreso / evento"], ["address", "Lugar"], ["pages", "Páginas"]] },
  misc: { nombre: "Otro", campos: [["howpublished", "Publicado en"], ["url", "URL"]] },
};

function formularioReferencia(alAgregar) {
  const tipo = el("select", {}, Object.entries(TIPOS_REF).map(([k, v]) => el("option", { value: k, text: v.nombre })));
  const comunes = [["clave", "Clave (para citar)"], ["author", "Autores (Nombre Apellido; separados por ;)"], ["title", "Título"], ["year", "Año"]];
  const cont = el("div", { class: "mini-form" });
  const dibujar = () => {
    const campos = [...comunes, ...TIPOS_REF[tipo.value].campos];
    cont.replaceChildren(el("label", {}, "Tipo", tipo), ...campos.map(([k, t, ti]) =>
      el("label", {}, t, el("input", { type: ti || "text", name: k }))),
      el("label", { class: "interruptor", style: "align-self:end" }, el("input", { type: "checkbox", name: "_institucional" }), "Autor institucional"),
      el("div", { style: "align-self:end" }, el("button", { class: "boton primario", type: "button", text: "Agregar referencia", onclick: agregar })));
  };
  const agregar = () => {
    const entradas = [...cont.querySelectorAll("input")];
    const institucional = entradas.find((i) => i.name === "_institucional").checked;
    const v = Object.fromEntries(entradas.filter((i) => !i.name.startsWith("_")).map((i) => [i.name, i.value.trim()]));
    if (!v.clave || !v.title) { aviso("La clave y el título son obligatorios", "error"); return; }
    const clave = v.clave.replace(/[^\w:-]/g, "_");
    delete v.clave;
    if (v.author) {
      // Personas: "Nombre Apellido; Nombre Apellido". Institución: se protege entre llaves.
      v.author = institucional ? `{${v.author}}`
        : v.author.split(";").map((a) => a.trim()).filter(Boolean).join(" and ");
    }
    const lineas = Object.entries(v).filter(([, x]) => x).map(([k, x]) => `  ${k.padEnd(12)} = {${x}},`);
    alAgregar(`\n@${tipo.value}{${clave},\n${lineas.join("\n")}\n}\n`, clave);
    cont.querySelectorAll("input").forEach((i) => { if (i.type === "checkbox") i.checked = false; else i.value = ""; });
  };
  tipo.addEventListener("change", dibujar);
  dibujar();
  return cont;
}

async function dibujarReferencias() {
  const panel = $("#panel-referencias");
  const bibs = E.doc.archivos.bib;
  if (!bibs.length) {
    panel.replaceChildren(el("div", { class: "tarjeta" }, el("div", { class: "tarjeta-cuerpo" },
      el("p", { class: "ayuda", text: "Este documento todavía no tiene un archivo de referencias." }),
      el("button", { class: "boton primario agregar", type: "button", text: "Crear referencias.bib", onclick: async () => {
        await api("POST", "/api/archivo", { ruta: `${E.doc.carpeta}/referencias.bib`, texto: "% Referencias en formato BibTeX\n", crear: true });
        await refrescarArchivos();
        dibujarReferencias();
      } }))));
    return;
  }
  const ruta = `${E.doc.carpeta}/${bibs[0]}`;
  if (!E.archivo || E.archivo.ruta !== ruta) {
    try {
      const r = await api("GET", `/api/archivo?ruta=${encodeURIComponent(ruta)}`);
      E.archivo = { ruta: r.ruta, texto: r.texto, sucio: false };
    } catch (e) { aviso(e.message, "error"); return; }
  }
  const claves = [...E.archivo.texto.matchAll(/@\w+\s*\{\s*([^,\s]+)\s*,/g)].map((m) => m[1]);
  let area;
  const barra = () => barraArchivo([el("span", { class: "ayuda", text: `${claves.length} referencia(s)` })]);
  area = areaEditor(E.archivo.texto, (v) => {
    E.archivo.texto = v;
    if (!E.archivo.sucio) { E.archivo.sucio = true; panel.querySelector(".barra-editor").replaceWith(barra()); }
  });
  const form = formularioReferencia((bib, clave) => {
    area.value = area.value.replace(/\s*$/, "\n") + bib;
    area.dispatchEvent(new Event("input"));
    aviso(`Referencia agregada. Cítala con @${clave} y guarda el archivo.`);
  });
  panel.replaceChildren(
    tarjeta("Agregar referencia", form, "ref:nueva", true),
    el("div", { class: "tarjeta" }, el("div", { class: "tarjeta-titulo" }, "Claves para citar",
      el("span", { class: "ayuda", text: "Escribe @clave en el contenido" })),
      el("div", { class: "tarjeta-cuerpo", style: "display:flex;flex-wrap:wrap;gap:6px" },
        claves.length ? claves.map((c) => el("button", { class: "boton chico", type: "button", text: `@${c}`,
          onclick: async () => { await navigator.clipboard.writeText(`@${c}`); aviso(`Copiado: @${c}`); } }))
          : el("span", { class: "ayuda", text: "Aún no hay referencias." }))),
    el("div", { class: "area-editor" }, barra(), area));
}

/* --- YAML ---------------------------------------------------------------------------- */

function dibujarYaml() {
  const panel = $("#panel-yaml");
  let texto = E.doc.yaml;
  let cambiado = false;
  const boton = el("button", { class: "boton chico primario", type: "button", text: "Guardar YAML", disabled: true,
    onclick: async () => {
      try {
        const r = await api("POST", "/api/documento", { ruta: E.doc.ruta, yaml: texto });
        E.doc.yaml = r.yaml;
        E.doc.datos = r.datos;
        E.datos = clonar(r.datos);
        cambiado = false;
        boton.disabled = true;
        dibujarCabecera();
        aviso("YAML guardado", "ok");
        cargarDocumentos();
      } catch (e) { aviso(e.message, "error"); }
    } });
  const area = areaEditor(texto, (v) => { texto = v; cambiado = true; boton.disabled = false; });
  panel.replaceChildren(el("div", { class: "area-editor", style: "min-height:100%" },
    el("div", { class: "barra-editor" }, el("span", { class: "nombre", text: E.doc.ruta }),
      el("span", { class: "ayuda", text: "Edición avanzada: el formulario usa estos mismos datos." }), boton), area));
}

/* --- generación y resultado ---------------------------------------------------------- */

async function generar() {
  if (!E.doc) return;
  const salidas = [...document.querySelectorAll("#chips-salidas input:checked")].map((i) => i.value);
  if (!salidas.length) { aviso("Elige al menos una salida", "error"); return; }
  if (E.archivo && E.archivo.sucio) await guardarArchivo();
  if (E.sucio) { try { await guardar({ silencioso: true }); } catch { return; } }
  const boton = $("#btn-generar");
  boton.classList.add("cargando");
  boton.disabled = true;
  const registro = $("#registro");
  try {
    const tema = E.doc.formato === "presentacion" ? $("#tema").value : null;
    const r = await api("POST", "/api/generar", { ruta: E.doc.ruta, salidas, tema });
    const nuevos = new Set(r.archivos.map((a) => a.ruta));
    E.generados = [...r.archivos, ...E.generados.filter((g) => !nuevos.has(g.ruta))];
    const pdf = r.archivos.find((a) => a.ext === "pdf");
    E.vista = (pdf || r.archivos[0]).ruta;
    registro.classList.toggle("oculto", !r.registro);
    registro.classList.remove("error");
    $("#registro-texto").textContent = r.registro || "";
    aviso(`Generado: ${r.archivos.map((a) => a.nombre).join(", ")}`, "ok");
    dibujarResultado();
  } catch (e) {
    registro.classList.remove("oculto");
    registro.classList.add("error");
    registro.open = true;
    $("#registro-texto").textContent = e.message;
    aviso("No se pudo generar. Revisa los mensajes.", "error");
  } finally {
    boton.classList.remove("cargando");
    boton.disabled = false;
  }
}

function dibujarResultado() {
  const pestanas = $("#pestanas-resultado");
  const vista = $("#vista");
  const lista = E.generados;
  if (!lista.length) {
    pestanas.replaceChildren();
    vista.replaceChildren(el("p", { class: "ayuda", text: "Genera el documento para ver aquí la vista previa." }));
    return;
  }
  if (!E.vista || !lista.some((g) => g.ruta === E.vista)) E.vista = (lista.find((g) => g.ext === "pdf") || lista[0]).ruta;
  pestanas.replaceChildren(...lista.map((g) => el("button", {
    class: g.ruta === E.vista ? "activa" : "", type: "button", title: g.nombre,
    text: g.ext.toUpperCase(), onclick: () => { E.vista = g.ruta; dibujarResultado(); },
  })));
  const g = lista.find((x) => x.ruta === E.vista);
  const abrir = el("button", { class: "boton chico", type: "button", text: "Abrir",
    onclick: () => api("POST", "/api/abrir", { ruta: g.ruta }).catch((e) => aviso(e.message, "error")) });
  const descargar = el("a", { class: "boton chico", href: urlArchivo(g.ruta, true), text: "Descargar" });
  if (g.ext === "pdf") {
    vista.replaceChildren(el("iframe", { src: urlArchivo(g.ruta), title: g.nombre }),
      el("div", { class: "acciones-archivo" }, el("span", { class: "ayuda", style: "margin-right:auto", text: g.nombre }), abrir, descargar));
  } else {
    const app = g.ext === "docx" ? "Word" : g.ext === "pptx" ? "PowerPoint" : "la aplicación";
    vista.replaceChildren(el("div", { class: "archivo-generado" },
      el("div", { class: `icono-archivo ${g.ext}`, text: g.ext.toUpperCase() }),
      el("strong", { text: g.nombre }),
      el("p", { class: "ayuda", text: `La vista previa está disponible para PDF. Abre el archivo en ${app} o descárgalo.` }),
      el("div", { class: "con-boton" }, abrir, descargar)));
    abrir.textContent = `Abrir en ${app}`;
  }
}

/* --- nuevo documento -------------------------------------------------------------- */

function abrirDialogoNuevo() {
  const dlg = $("#dialogo-nuevo");
  const sel = $("#nuevo-formato");
  sel.replaceChildren(...E.estado.formatos.map((f) => el("option", { value: f.nombre, text: NOMBRE_FORMATO[f.nombre] || f.nombre })));
  const describir = () => {
    const f = E.estado.formatos.find((x) => x.nombre === sel.value);
    $("#nuevo-descripcion").textContent = `${f.descripcion}. Salidas: ${f.salidas.join(", ")}.`;
  };
  sel.onchange = describir;
  describir();
  $("#nuevo-carpeta").value = "";
  dlg.showModal();
  dlg.onclose = async () => {
    if (dlg.returnValue !== "crear") return;
    try {
      const r = await api("POST", "/api/nuevo", { formato: sel.value, carpeta: $("#nuevo-carpeta").value });
      await cargarDocumentos();
      await abrirDocumento(r.ruta, { forzar: true });
      aviso("Documento creado", "ok");
    } catch (e) { aviso(e.message, "error"); }
  };
}

iniciar().catch((e) => aviso(e.message, "error"));
