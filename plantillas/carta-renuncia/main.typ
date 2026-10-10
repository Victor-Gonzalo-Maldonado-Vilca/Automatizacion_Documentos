#let d = yaml("/documentos/ejemplo-carta-renuncia/carta.yaml")
#let dest = d.at("destinatario")
#let rem = d.at("remitente")
#let ren = d.at("renuncia")

#set page(paper: "a4", margin: 2.5cm)
#set text(font: "Times New Roman", size: 12pt, lang: "es")
#set par(justify: true, leading: 0.8em)

//Lugar y Fecha
#align(right)[Arequipa, 11 de octubre de 2026]

// Destinatario
*Sr. Juan Perez*\ 
Gerente\ 
Leche Gloria\
Presente.-

#v(0.8cm)

*Asunto:* Carta de renuncia voluntaria e irrevocable

#v(0.6cm)

Yo, *Victor Gonzalo Maldonado Vilca*, identificado con DNI N.° 76602403, *Desarrollador de Software* en el área de *Frontend*, me dirijo a usted con la finalidad de presentar mi renuncia irrevocable al puesto que ocupo en la organización.
Esta decisión responde a la necesidad de asumir nuevos compromisos de carácter estrictamente académico y formativo, los cuales resultan incompatibles con mi jornada laboral actual. En ese sentido, solicito la exoneración del plazo de preaviso de 30 días fijado por ley, siendo mi última fecha efectiva de labores el *25 de octubre de 2026*.

Asimismo, expreso mi sincero agradecimiento a la empresa y a mi equipo por la confianza brindada y el grato ambiente de trabajo durante mi permanencia en la institución.

Sin otro particular, quedo a su disposición para coordinar la entrega de mi puesto y pendientes.

Atentamente,
#v(2.5cm)
// Bloque de firma centrado
#align(center)[
    #line(length: 6.5cm)
    #v(0.3cm)
    *Victor Gonzalo Maldonado Vilca*\
    DNI: 76602403\
    Desarrollador de Software
]
