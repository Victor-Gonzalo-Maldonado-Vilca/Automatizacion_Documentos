#import "/plantillas/informe-academico/componentes.typ": *

= 1. Tablas

Las tablas usan el estilo de la plantilla: encabezado de color durazno, bordes grises
y texto de 10 puntos. El título va arriba, en negrita. La @tab:requerimientos muestra
un ejemplo.

#tabla(
  columnas: (auto, 1fr, 2fr, auto),
  encabezado: ([Código], [Nombre], [Descripción], [Prioridad]),
  [*RF-01*], [Primer requerimiento], [Descripción detallada del primer requerimiento.], [Alta],
  [*RF-02*], [Segundo requerimiento], [Descripción detallada del segundo requerimiento.], [Media],
  [*RF-03*], [Tercer requerimiento], [Descripción detallada del tercer requerimiento.], [Baja],
  pie: [Matriz de requerimientos],
) <tab:requerimientos>

= 2. Figuras

Las figuras llevan su pie debajo, con el número en negrita y la descripción en cursiva,
como en la @fig:diagrama.

#captura("imagenes/captura_ejemplo.png", [Diagrama o captura de ejemplo], ancho: 80%) <fig:diagrama>

= 3. Código y ecuaciones

#codigo(desde: "codigo/Rotador.cs", pie: [Fragmento de código de ejemplo])

También se pueden incluir ecuaciones numeradas:

$ v = frac(Delta x, Delta t) $ <eq:velocidad>

#nota[Los recuadros de nota sirven para observaciones importantes.]
