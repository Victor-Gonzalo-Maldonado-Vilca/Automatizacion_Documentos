#let d = if "datos" in sys.inputs {
  json(sys.inputs.at("datos"))                            
} else {
  yaml("/documentos/ejemplo-carta-renuncia/carta.yaml")   
}

#let dest = d.at("destinatario")
#let rem = d.at("remitente")
#let ren = d.at("renuncia")

#let vacio(v) = v == none or str(v).trim() == ""
#let req(v, nombre) = if vacio(v) {
  text(fill: red)[*[FALTA: #nombre]*]
} else { v }

#set page(paper: "a4", margin: 2.5cm)
#set text(font: "Times New Roman", size: 12pt, lang: "es")
#set par(justify: true, leading: 0.8em, spacing: 1.4em)

//Lugar y Fecha
#align(right)[#req(d.at("lugar"), "Lugar"), #req(d.at("fecha"), "Fecha")]
// Destinatario
*#req(dest.at("tratamiento"), "Tratamiento") #req(dest.at("nombre"), "Nombre_Destinatario")*\ 
#req(dest.at("cargo"), "Cargo_Destinatario")\ 
#req(dest.at("organizacion"), "Organizacion o Empresa")\
Presente.-

#v(0.8cm)

*Asunto:* Carta de renuncia voluntaria e irrevocable

#v(0.6cm)

Yo, *#req(rem.at("nombre"), "Nombre_Remitente")*, identificado con DNI N.° #req(rem.at("dni"), "DNI"), *#req(rem.at("cargo"), "Cargo_Remitente")* en el área de *#req(rem.at("area"), "Area_Remitente")*, me dirijo a usted con la finalidad de presentar mi renuncia irrevocable al puesto que ocupo en la organización.
#if not vacio(ren.at("motivo")) [#ren.at("motivo").]
#if str(ren.at("exoneracion_preaviso", default: "false")) == "true" [
    En ese sentido, solicito la exoneración del plazo de preaviso de 30 días fijado por ley,
] else [
    En ese sentido, cumpliré con el plazo de preaviso de 30 días establecido por ley,
]
siendo mi última fecha efectiva de labores el *#req(ren.at("fecha_efectiva"), "Fecha_Efectiva")*.

#let agr = d.at("agradecimientos", default: none)
#if type(agr) == array {
    for a in agr.filter(x => not vacio(x)) [
        #a\
    ]
}

Sin otro particular, quedo a su disposición para coordinar la entrega de mi puesto y pendientes.

Atentamente,
#v(2.5cm)
// Bloque de firma centrado
#align(center)[
    #line(length: 6.5cm)
    #v(0.3cm)
    *#req(rem.at("nombre"), "Nombre_Remitente")*\
    DNI: #req(rem.at("dni"), "DNI")\
    #req(rem.at("cargo"), "Cargo_Remitente")
]
