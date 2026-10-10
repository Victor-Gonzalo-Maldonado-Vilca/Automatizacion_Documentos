#import "/plantillas/informe-laboratorio/componentes.typ": *

Respuesta de la tercera pregunta con un fragmento de código en línea, como
`transform.Rotate()`, y un bloque corto:

#codigo(titulo: "Ejemplo.cs")[```cs
void Update() {
    transform.Rotate(0f, velocidad * Time.deltaTime, 0f);
}
```]
