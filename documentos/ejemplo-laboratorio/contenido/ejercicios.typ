#import "/plantillas/informe-laboratorio/componentes.typ": *

= Ejercicio 1: Descripción del problema

Aquí se redacta la solución del ejercicio. El texto se justifica automáticamente y
usa la misma fuente y tamaño de la plantilla. Se pueden citar fuentes en formato
IEEE escribiendo su clave, por ejemplo @typst_docs, o varias a la vez @ieee_guide @python_docs.

Para insertar una captura de pantalla se coloca la imagen en la carpeta
`imagenes/` y se usa `captura`. La figura se numera sola y puede referenciarse
en el texto, como en la @fig:ejemplo.

#captura("imagenes/captura_ejemplo.png", [Captura de ejemplo con borde y pie numerado.], ancho: 75%) <fig:ejemplo>

== Resultados obtenidos

Las tablas usan el mismo estilo del informe: encabezado rojo y bordes negros finos.
La @tab:resultados resume los valores medidos.

#tabla(
  columnas: (auto, 1fr, auto),
  encabezado: ([Prueba], [Descripción], [Resultado]),
  [1], [Caso base con datos de entrada válidos], [Correcto],
  [2], [Caso límite con valores máximos], [Correcto],
  [3], [Entrada inválida controlada], [Error esperado],
  pie: [Resultados de las pruebas realizadas.],
) <tab:resultados>

El código se puede escribir directamente o cargar desde un archivo de la carpeta
`codigo/`; en ambos casos se muestran los números de línea y el resaltado de sintaxis.

#codigo(desde: "codigo/Rotador.cs", pie: [Script de ejemplo cargado desde archivo.])

También se admiten ecuaciones numeradas:

$ theta_(t+1) = theta_t + omega dot Delta t $ <eq:rotacion>

donde $omega$ es la velocidad angular y $Delta t$ el tiempo entre frames (@eq:rotacion).

#nota[Los recuadros de nota sirven para observaciones o advertencias importantes.]
